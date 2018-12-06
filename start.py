import falcon
import re
import requests
import json
import datetime
import os
import jinja2
import shutil
from configparser import ConfigParser
from time import sleep
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from scrapy.utils.project import get_project_settings
from sparepart.models import ScrapingJob
from crawler_queue import CrawlerQueue


SCRAPY_SETTINGS = get_project_settings()

CRAWLER_DELAY = {
    'isuzu': os.environ.get('DELAY_ISUZU', 1),
    'suzuki': os.environ.get('DELAY_SUZUKI', 1),
    'daihatsu': os.environ.get('DELAY_DAIHATSU', 1),
    'megazip': os.environ.get('DELAY_MEGAZIP', 15),
    'parts.com': os.environ.get('DELAY_PARTS', 15),
}

scrapyd_config = ConfigParser()
scrapyd_config.read('scrapyd.conf')

SCRAPYD_HOST = 'http://{}:{}'.format('localhost',
                                     scrapyd_config['scrapyd']['http_port'])

# create database session
CONNECTION_STRING = os.environ.get('CONNECTION_STRING')
if CONNECTION_STRING:
    engine = create_engine(CONNECTION_STRING, echo=True)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

import logging
logger = logging.getLogger(__name__)


class SQLAlchemySessionManager:
    """
    Create a scoped session for every request and close it when the request
    ends.
    """

    def __init__(self, Session):
        self.Session = Session

    def process_resource(self, req, resp, resource, params):
        resource.session = self.Session()

    def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(resource, 'session'):
            if not req_succeeded:
                resource.session.rollback()
            Session.remove()


class AuthMiddleware(object):

    def process_request(self, req, resp):
        auth_header = req.get_header('Authorization')
        if auth_header:
            req.context['authenticated'] = auth_header.split(' ')[-1] == 'dXNlcm5hbWU6cGFzc3dvcmQ='


def validate_auth(req, resp, resource, params):
    description = 'Please provide valid authentication header.'
    challenges = ['Authorization: Basic ...']
    if 'authenticated' not in req.context or not req.context['authenticated']:
        raise falcon.HTTPUnauthorized('Authentication required',
                                      description,
                                      challenges,
                                      href='http://docs.example.com/auth')


def save_job(session, job):
    """
    save new job to database
    """
    try:
        session.add(job)
        session.commit()

    except Exception as e:
        logger.error("{} - {}".format(type(e), str(e)))
        session.rollback()
        raise

    finally:
        session.close()


def get_job(session, job_id):
    """
    get job from database
    """
    try:
        return session.query(ScrapingJob.jobdir).filter_by(id=job_id).first()[0]
    except Exception as e:
        logger.error("{} - {}".format(type(e), str(e)))
        raise


def is_job_slot_available(spider, job_list=None):
    """
    check if job slot is available, max 1 job for each spider
    """
    if not job_list:
        response = requests.get('{}/listjobs.json?project=default'.format(SCRAPYD_HOST))
        data = response.json()
        job_list = data['pending'] + data['running']

    for job in job_list:
        for k, v in job.items():
            if k == 'spider' and v == spider:
                break
        else:
            continue

        # job slot for spider not available
        # response message here
        print('job slot not available')
        return False

    else:  # job slot available
        print('job slot available')
        return True


def schedule_job(spider, params, session):
    """
    schedule crawling job
    """
    scheduler_url = '{}/schedule.json'.format(SCRAPYD_HOST)
    if isinstance(params, bytes):
        params = params.decode()

    if not isinstance(params, dict):
        params = json.loads(params)

    options = params.copy()
    options.update({'spider': spider, 'project': 'default'})
    response = requests.post(scheduler_url, options)
    data = response.json()
    if 'status' in data:
        status = data['status']
    if status == 'ok':
        success = True
        msg = 'Scheduled crawling for spider {}. JobID ({})'.format(spider, data['jobid'])
        index = None
        for k, v in enumerate(params['setting']):
            if 'JOBDIR' in v:
                index = k
                break
        jobdir = params['setting'][index].split('=')[-1]

        job = ScrapingJob(**{'id': data['jobid'], 'spider': spider, 'start': datetime.datetime.now(),
                             'status': 'started', 'input_param': json.dumps(params), 'jobdir': jobdir})
        if session:
            save_job(session, job)
    else:
        status = data['status']
        msg = data['message']

    return success, status, msg


def get_valid_filename(s):
    str_ = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', str_)


class Crawler(object):
    job_directory = 'data/crawljobs'
    date_format = '%Y_%m_%d_%H_%M_%S'
    max_jobdir_length = int(os.environ.get('MAX_JOBDIR_LENGTH', 10))

    def __init__(self):
        self.queue = CrawlerQueue()

    @falcon.before(validate_auth)
    def on_get(self, req, resp):

        params = req.params

        spider = params.get('spider', None)
        merk = params.get('merk', None)

        if not spider or not merk:
            resp.body = json.dumps({'error': 'parameter `spider` and `merk` must not be empty'}, indent=4)
            resp.status = falcon.HTTP_400
            return

        if merk.lower() == 'suzuki' and isinstance(params.get('model', None), list):
            params['model'] = " ".join([a for a in params.get('model', [])])

        delay = params.get('delay', None)
        model = params.get('model', None)
        if not spider:
            raise falcon.HTTPBadRequest('Missing Spider', 'Missing spider in query string parameters.')
        if not merk:
            raise falcon.HTTPBadRequest('Missing Merk', 'Missing merk in query string parameters.')
        if not model:
            raise falcon.HTTPBadRequest('Missing Model', 'Missing model in query string parameters.')

        # cleanse params
        param_list = ['spider', 'merk', 'model', 'tahun', 'year', 'mesin', 'engine', 'varian', 'type', 'tipe', 'delay']
        param_list += ['region']
        for k in list(params.keys()):
            if k not in param_list:
                del params[k]

        # add delay parameter
        if not delay:
            delay = CRAWLER_DELAY[spider]
        params['setting'] = ['DOWNLOAD_DELAY={}'.format(delay)]
        job_dir = '{}/{}_{}_{}_{}'.format(self.job_directory, spider, merk, get_valid_filename(model),
                                          datetime.datetime.now().strftime(self.date_format))

        params['jobdir'] = job_dir
        params['setting'] += ['JOBDIR={}'.format(job_dir)]

        def sort_by_datetime(datestring):
            splitup = datestring.split('_')[-6:]
            dttm = '_'.join(splitup)
            return datetime.datetime.strptime(dttm, self.date_format)

        # housekeeping check for CRAWLING JOBDIR
        spiderjoblist = []
        for itm in os.listdir(self.job_directory):
            if itm.split('_')[0] == spider:
                spiderjoblist.append(itm)
        if len(spiderjoblist) > self.max_jobdir_length:
            spiderjoblist.sort(key=sort_by_datetime, reverse=True)
            while len(spiderjoblist) > self.max_jobdir_length:  # max jobdir length as settings
                shutil.rmtree('{}/{}'.format(self.job_directory, spiderjoblist.pop()))

        # add job for this spider to queue db
        self.queue.push(spider, params)

        # check if there is available job slot for current spider
        response = requests.get('{}/listjobs.json?project=default'.format(SCRAPYD_HOST))
        data = response.json()
        pending_running_jobs = data['pending'] + data['running']
        if not is_job_slot_available(spider, pending_running_jobs):  # queue crawling job
            success = True
            status = 'ok'
            msg = 'Crawling job has been added to queue list'

        else:  # schedule crawling job

            try:
                params, date_added = self.queue.pop(spider)  # get next job params
                session = self.session if hasattr(self, 'session') else None
                success, status, msg = schedule_job(spider, params, session)

            except Exception as e:
                success = False
                status = 'not ok'
                msg = str('{} - {}'.format(type(e), str(e)))

        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'success': success, 'status': status, 'message': msg}, indent=4)


class CrawlJob(object):

    def on_get(self, req, resp):

        # limit scheduled crawler process
        response = requests.get('{}/jobs'.format(SCRAPYD_HOST))
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        text = response.text
        text = re.sub('<title>Scrapyd</title>', '<title>Crawling Jobs</title>', text)
        text = re.sub('<h1>Jobs</h1>', '<h1>Crawling Jobs</h1>', text)
        text = re.sub('<p>.*Go back.*</p>', '', text)
        text = text.replace("<tr><th colspan='8' style='background-color: #ddd'>Pending</th></tr>", '')
        resp.body = text


class Log(object):

    def on_get(self, req, resp, spider, log_file):
        response = requests.get('{}/logs/default/{}/{}'.format(SCRAPYD_HOST, spider, log_file))
        resp.status = falcon.HTTP_200
        text = response.text
        resp.body = text


def load_template(name):
    path = os.path.join('templates', name)
    with open(os.path.abspath(path), 'r') as fp:
        return jinja2.Template(fp.read())


class QueueList(object):
    """Crawl Queue Resource"""
    def __init__(self):
        self.queue = CrawlerQueue()

    def on_get(self, req, resp):
        # render template
        template = load_template('crawler_queue.html')

        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.body = template.render(spiders=self.queue.get_all_queue())


class CancelQueue(object):
    """Cancel Crawling Queue"""
    def __init__(self):
        self.queue = CrawlerQueue()

    def on_get(self, req, resp, spider=None, queue_id=None):
        success, status, msg = False, 'ok', '{} queue with id:{} '.format(spider, queue_id)
        try:
            # remove queue from db
            if self.queue.delete(spider, queue_id):
                success = True
                msg += 'deleted'
            else:
                msg += 'not found'

        except Exception as e:
            success = False
            status = 'exception occured.'
            msg = str('{} - {}'.format(type(e), str(e)))
            print('{} - {}'.format(type(e), str(e)))

        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'success': success, 'status': status, 'message': msg}, indent=4)


class CancelJob(object):
    """Cancel Crawling Job"""
    def on_get(self, req, resp, job_id=None):
        success, status, msg = False, 'ok', 'job with id:{} '.format(job_id)
        try:
            # stop running crawling
            cancel_url = '{}/cancel.json'.format(SCRAPYD_HOST)
            options = {'project': 'default', 'job': job_id}
            response = requests.post(cancel_url, options)
            data = response.json()
            if data['status'] == 'ok' and data['prevstate']:
                success = True
                msg += ' is being canceled. please wait a moment.'
            else:
                msg = 'cancelling job failed.'

        except Exception as e:
            success = False
            status = 'exception occured.'
            msg = str('{} - {}'.format(type(e), str(e)))
            print('{} - {}'.format(type(e), str(e)))

        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'success': success, 'status': status, 'message': msg}, indent=4)


class CrawlerQueueCheck(object):
    def __init__(self):
        self.queue = CrawlerQueue()

    def on_get(self, req, resp, spider=None, job_id=None):

        delay = 5
        sleep(delay)  # add delay
        print('checking queue for {}...'.format(spider))
        success, status, msg = False, 'ok', 'crawler queue checked'
        try:
            if is_job_slot_available(spider):  # schedule new crawling job
                params, date_added = self.queue.pop(spider)  # get next job params
                session = self.session if hasattr(self, 'session') else None
                success, status, msg = schedule_job(spider, params, session)

        except Exception as e:
            success = False
            status = 'exception occured.'
            msg = str('{} - {}'.format(type(e), str(e)))

        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'success': success, 'status': status, 'message': msg}, indent=4)


class TestResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('\nTwo things awe me most, the starry sky '
                     'above me and the moral law within me.\n'
                     '\n'
                     '    ~ Immanuel Kant\n\n')


# falcon.API instances are callable WSGI apps
middleware_to_use = [AuthMiddleware()]
if CONNECTION_STRING:
    middleware_to_use.append(SQLAlchemySessionManager(Session))

app = falcon.API(middleware=middleware_to_use)

# Resources are represented by long-lived class instances
crawler = Crawler()
crawljob = CrawlJob()
log = Log()
crawler_queue_check = CrawlerQueueCheck()
queue_list = QueueList()
cancel_queue = CancelQueue()
cancel_job = CancelJob()

# will handle all requests to the '/crawl' URL path
app.add_route('/crawl', crawler)

# will handle all requests to the '/jobs' URL path
app.add_route('/jobs', crawljob)

# will handle all requests to the '/log' URL path
app.add_route('/logs/default/{spider}/{log_file}', log)

# check and update crawling queue
app.add_route('/crawler_queue_check/{spider}/{job_id}', crawler_queue_check)
app.add_route('/queue_list', queue_list)

# cancel crawl job
app.add_route('/cancel_job/{job_id}', cancel_job)

# cancel queue
app.add_route('/cancel_queue/{spider}/{queue_id}', cancel_queue)

# Resources are represented by long-lived class instances
test = TestResource()

# things will handle all requests to the '/test' URL path
app.add_route('/test', test)
