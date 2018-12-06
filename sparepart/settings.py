# -*- coding: utf-8 -*-

# Scrapy settings for sparepart project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import os
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
print('PROJECT_DIR::{}', str(PROJECT_DIR))
BOT_NAME = 'sparepart'

SPIDER_MODULES = ['sparepart.spiders']
NEWSPIDER_MODULE = 'sparepart.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'sparepart (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
if os.environ.get('DOWNLOAD_DELAY'):
    DOWNLOAD_DELAY = os.environ.get('DOWNLOAD_DELAY')
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'sparepart.middlewares.SparepartSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'sparepart.middlewares.SparepartDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 180
if os.environ.get('AUTOTHROTTLE_MAX_DELAY'):
    DOWNLOAD_DELAY = os.environ.get('AUTOTHROTTLE_MAX_DELAY')
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

EXTENSIONS = {
    'scrapy.extensions.throttle.AutoThrottle': 1,
    'scrapy.extensions.closespider.CloseSpider': 2,
}


# Retry many times since proxies often fail
RETRY_TIMES = 3
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408, 429]


# image pipeline
# ITEM_PIPELINES = {
#     'scrapy.pipelines.images.ImagesPipeline': 1,
# }
IMAGES_STORE = '{}/scraped_images'.format(PROJECT_DIR)

DUPEFILTER_DEBUG = False

CONNECTION_STRING = os.environ.get('CONNECTION_STRING')

CRAWL_INFO_LOG_LEVEL_NUM = 35

# set pause retry for status 429 (in minutes)
PAUSE_RETRY_429 = 15
if os.environ.get('PAUSE_RETRY_429'):
    PAUSE_RETRY_429 = os.environ.get('PAUSE_RETRY_429')

if os.environ.get('LOG_LEVEL'):
    LOG_LEVEL = os.environ.get('LOG_LEVEL')
else:
    LOG_LEVEL = 'DEBUG'

if LOG_LEVEL == 'DEBUG':
    CLOSESPIDER_ITEMCOUNT = 10
