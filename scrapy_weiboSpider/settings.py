# -*- coding: utf-8 -*-
import json
from spider_tool import comm_tool
import os

FEED_EXPORT_ENCODING = "gbk"

LOG_LEVEL = 'INFO'
# 指定Redis的主机名和端口
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

CONFIG_PATH = f"configs{os.sep}dufault_config.json"

# 自定义中间件设置
JSON_FIELD_RETRY_MAX_RETRIES = 5  # 响应中json字段缺失的最大重试次数

DEPTH_PRIORITY = -1
SCHEDULER_QUEUE_KEY = "weibo_default:requests"

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# "SCHEDULER_DUPEFILTER_KEY": f'{keyword}:dupefilter',

DUPEFILTER_CLASS = "scrapy.dupefilters.RFPDupeFilter"
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# DUPEFILTER_CLASS = "T_filter.Filtre1.RFPDupeFilter"
# 关闭时保留调度器和去重记录
SCHEDULER_PERSIST = True
# 调度策略
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

RETRY_TIMES = 4
LOG_FILE = comm_tool.get_log_path()

RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 400]

BOT_NAME = 'scrapy_weiboSpider'
SPIDER_MODULES = ['scrapy_weiboSpider.spiders']
NEWSPIDER_MODULE = 'scrapy_weiboSpider.spiders'

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 1.5
CONCURRENT_REQUESTS = 12
CONCURRENT_REQUESTS_PER_DOMAIN = 12
CONCURRENT_REQUESTS_PER_IP = 12

COOKIES_ENABLED = True

DEFAULT_REQUEST_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
}
SPIDER_MIDDLEWARES = {
    'scrapy_weiboSpider.middlewares.ScrapyWeibospiderSpiderMiddleware': 543,
}
DOWNLOADER_MIDDLEWARES = {
    # 'scrapy_weiboSpider.middlewares.ScrapyWeibospiderDownloaderMiddleware': 543,
    'scrapy_weiboSpider.middlewares.LoginStatusMiddleware': 550,
    'scrapy_weiboSpider.middlewares.ResponseStatusHandlerMiddleware': 540,
    'scrapy_weiboSpider.middlewares.Ok1RetryMiddleware': 530,
    'scrapy_weiboSpider.middlewares.JsonFieldRetryMiddleware': 520,

}
ITEM_PIPELINES = {
    'scrapy_weiboSpider.pipelines.ScrapyWeibospiderPipeline': 300,
}
