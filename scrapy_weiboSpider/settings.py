# -*- coding: utf-8 -*-
import json
import time
import re
import os
import msvcrt
from scrapy_weiboSpider.config_path_file import config_path
import spider_tool

config = json.load(open(config_path, "r", encoding="utf-8"))

FEED_EXPORT_ENCODING = "gbk"

# 指定Redis的主机名和端口
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

# redis key
redis_key = spider_tool.get_key_word(config, False)
SCHEDULER_DUPEFILTER_KEY = '{}:dupefilter'.format(redis_key)
SCHEDULER_QUEUE_KEY = "{}:requests".format(redis_key)

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# DUPEFILTER_CLASS = "T_filter.Filtre1.RFPDupeFilter"
# 将Requests队列持久化到Redis，可支持暂停或重启爬虫
SCHEDULER_PERSIST = True
# Requests的调度策略，默认优先级队列
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

RETRY_TIMES = 4
LOG_FILE = "./log/default_log.log"
LOG_LEVEL = 'INFO'

RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 400]

BOT_NAME = 'scrapy_weiboSpider'
SPIDER_MODULES = ['scrapy_weiboSpider.spiders']
NEWSPIDER_MODULE = 'scrapy_weiboSpider.spiders'

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 20
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

COOKIES_ENABLED = True

DEFAULT_REQUEST_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
}
SPIDER_MIDDLEWARES = {
    'scrapy_weiboSpider.middlewares.ScrapyWeibospiderSpiderMiddleware': 543,
}
DOWNLOADER_MIDDLEWARES = {
    'scrapy_weiboSpider.middlewares.ScrapyWeibospiderDownloaderMiddleware': 543,
}
ITEM_PIPELINES = {
    'scrapy_weiboSpider.pipelines.ScrapyWeibospiderPipeline': 300,
}
