import os
import requests
import schedule
import time
from requests.exceptions import ReadTimeout
from crawler_queue import SPIDER_LIST

API_PORT = os.environ.get('API_PORT')


def queue_check():
    jobid = 0
    for spider in SPIDER_LIST:
        try:
            response = requests.get('http://localhost:{}/crawler_queue_check/{}/{}'.format(API_PORT, spider, jobid),
                                    timeout=(10, 1))
        except ReadTimeout as e:
            print('{} - {}'.format(type(e), str(e)))

    print('polling queue check finished..')

# schedule.every(10).seconds.do(queue_check)
# schedule.every(10).minutes.do(queue_check)
schedule.every().hour.do(queue_check)
# schedule.every().day.at("10:30").do(queue_check)
# schedule.every(5).to(10).days.do(queue_check)
# schedule.every().monday.do(queue_check)
# schedule.every().wednesday.at("13:15").do(queue_check)

while True:
    schedule.run_pending()
    time.sleep(1)
