import datetime
import os.path
import logging
import requests
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from requests.exceptions import ReadTimeout
from scrapy.spiders import CrawlSpider
from sqlalchemy.orm import sessionmaker, scoped_session
from ..models import db_connect, ScrapingJob
from scrapy.utils.project import get_project_settings
from ..helpers import read_file

LOG_LEVEL_NUM = get_project_settings().get("CRAWL_INFO_LOG_LEVEL_NUM")
logging.addLevelName(LOG_LEVEL_NUM, "CRAWL_INFO")

PROJECT_DIR = get_project_settings().get("PROJECT_DIR")
ROOT_DIR = os.path.abspath(os.path.join(PROJECT_DIR, os.pardir))

API_PORT = os.environ.get('API_PORT')


class BaseSpider(CrawlSpider):

    def __init__(self, *args, **kwargs):
        self.log_lvl = LOG_LEVEL_NUM
        if kwargs.get('tahun', None):
            kwargs.update({'year': kwargs.get('tahun')})
        if kwargs.get('tipe', None):
            kwargs.update({'varian': kwargs.get('tipe')})
        if kwargs.get('mesin', None):
            kwargs.update({'engine': kwargs.get('mesin')})
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.logger.debug(':::::args:::::  {}'.format(str(args)))
        self.logger.debug(':::::kwargs::::: {}'.format(str(kwargs)))

        # check required argument
        for attr in ['merk', 'model']:
            if attr not in self.__dict__:
                self.logger.error('Attr {} is missing'.format(attr))
                raise Exception('Attr {} is missing'.format(attr))

        info = '----Start Spider {}---- '.format(self.name)

        for itm in self.__dict__:
            if itm not in ['_rules', 'crawler', 'settings', '_follow_links', 'download_delay', 'log_lvl']:
                info += ', {}:{}'.format(itm, self.__dict__[itm])
        self.logger.log(self.log_lvl, info)

    def parse(self, response):
        if response.status != 200:
            self.logger.warning('Status Code {} when trying to crawl {}'.format(response.status, response.url))


    def closed(self, reason):
        self.logger.log(self.log_lvl, 'statistics : {}'.format(str(self.crawler.stats._stats)))

        if hasattr(self, '_job') and os.environ.get('CONNECTION_STRING'):
            engine = db_connect()
            Session = scoped_session(sessionmaker(bind=engine))
            update_session = Session()

            try:
                update_session.query(ScrapingJob).filter(ScrapingJob.id == str(self._job)). \
                    update({'reason': reason, 'status': 'finished', 'finish': datetime.datetime.utcnow()})
                update_session.commit()

                log_file_path = '{}/logs/default/{}/{}.log'.format(ROOT_DIR, self.name, self._job)
                update_session.query(ScrapingJob).filter(ScrapingJob.id == str(self._job)). \
                    update({'log': read_file(log_file_path)})

                update_session.commit()
                update_session.flush()

            except AttributeError as e:
                self.logger.warning("{} - {}".format(type(e), str(e)))
            except Exception as e:
                self.logger.error("{} - {}".format(type(e), str(e)))
                print("{} - {}".format(type(e), str(e)))
                update_session.rollback()
            finally:
                update_session.close()

        # check crawler queue
        try:
            self.logger.log(self.log_lvl, 'updating queue for crawler {}'.format(self.name))
            requests.get(
                'http://localhost:{}/crawler_queue_check/{}/{}'.format(API_PORT, self.name, self._job),
                timeout=(10, 1)
            )
        except ReadTimeout:
            self.logger.log(self.log_lvl, 'finish updating queue for crawler {}'.format(self.name))

        except Exception as e:
            print('Exception @ closed function. {} - {}'.format(type(e), str(e)))
            self.logger.log(self.log_lvl, 'Exception @ closed function. {} - {}'.format(type(e), str(e)))
