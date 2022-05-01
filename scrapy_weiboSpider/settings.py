# -*- coding: utf-8 -*-
import json
import time
import re
import os
import msvcrt
from scrapy_weiboSpider.config_path_file import config_path


def get_log_path(id=0):
    log_dir = "./log"
    suffix = ".log"
    base_filename = time.strftime("%m%d", time.localtime())

    p_log_path = log_dir + "/" + base_filename + "_s{}" + suffix
    if id:
        log_path = p_log_path.format(id)
        return log_path
    else:
        p_log_path = log_dir + "/" + base_filename + "_{}" + suffix
        n = 1
        while True:
            log_path = p_log_path.format(n)
            if not os.path.exists(log_path):
                return log_path
            else:
                n += 1


log_path = get_log_path()


def t_is_a_early_than_b(a, b, can_equal):
    """
    时间比较
    :param a: 毫秒时间戳(13位)或 "%Y-%m-%d %H:%M"格式的字符串
    :param b: 毫秒时间戳(13位)或 "%Y-%m-%d %H:%M"格式的字符串
    :param can_equal: 时间相等时返回True还是False
    :return: int
    """
    patten = "%Y-%m-%d %H:%M"
    if type(a) == str:
        time_a = time.strptime(a, patten)
        timestamp_a = time.mktime(time_a) * 1000
    elif type(a) == int:
        timestamp_a = a
    else:
        print("参数a应为int或str类型，返回0")
        return 0

    if type(b) == str:
        time_b = time.strptime(b, patten)
        timestamp_b = time.mktime(time_b) * 1000
    elif type(b) == int:
        timestamp_b = b
    else:
        print("参数a应为int或str类型,返回0")
        return 0

    result = timestamp_b - timestamp_a

    if can_equal:
        return result >= 0
    else:
        return result > 0


# Scrapy settings for scrapy_weiboSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html


def check_config():
    """
    配置文件检查
    :return:
    """
    print("检查配置文件")
    config_str = open(config_path, "r", encoding="gbk").read()
    config = json.loads(config_str, encoding="utf-8")
    # 个人主页模式
    if config["mode"] == 1:
        print("保存个人主页模式")
        t_config = config["personal_homepage_config"]
        if not t_config["user_id"]:
            print("id 为空")
            return False
        # 参数检查
        if not isinstance(t_config["get_all_comment"], int, ):
            print("get_all_comment 应为 int")
            return False
        if not isinstance(t_config["get_all_r_comment"], int):
            print("get_all_r_comment 应为 int")
            return False

        # 时间范围功能参数检查
        if t_config["time_range"]["enable"]:
            start_time = t_config["time_range"]["start_time"]
            stop_time = t_config["time_range"]["stop_time"]
            for time1 in [start_time, stop_time]:

                if not (isinstance(time1, int) or isinstance(time1, str)):
                    print("start_time/stop_time应为int或str")
                    return False

                if isinstance(time1, str):
                    patten = "%Y-%m-%d %H:%M"
                    try:
                        time.strptime(time1, patten)
                    except:
                        print("start_time/stop_time为str时，应该为%Y-%m-%d %H:%M格式")
                        return False
            if (start_time and stop_time) and not t_is_a_early_than_b(start_time, stop_time, False):
                print("时间范围设定错误（开始时间晚于结束时间）")
                return False
    # 搜索模式参数检查
    elif config["mode"] == 2:
        print("搜索模式")
        t_config = config["search_config"]
        if not t_config["search_code"]:
            print("搜索关键词不能为空")
            return False
        print("这个模式的功能还没开始写")
        return False

    # 评论实时更新模式参数检查
    elif config["mode"] == 3:
        print("评论监控模式")
        t_config = config["single_weibo_with_comment_real-time_updates_config"]
        if not t_config["weibo_url"]:
            print("微博链接不能为空")
            return False
        print("评论实时爬取模式")
        print("这个模式的功能还没开始写")
        return False


    # 模式编号错误
    else:
        mode_id = config["mode"]
        print("没有序号为{}的模式".format(mode_id))
        return False

    return True


def get_key_word(user_Chinese_symbols=True):
    """
    通过配置文件生成存到redis中key的名字
    :param user_Chinese_symbols:将时间设置中英文":"符替换为中文"："
    :return:
    """
    config_str = open(config_path, "r", encoding="gbk").read()
    config = json.loads(config_str, encoding="utf-8")
    key_word = ""
    if config["mode"] == 1:
        key_word = ""
        t_config = config["personal_homepage_config"]
        if t_config["user_name"]:
            key_word += "[" + t_config["user_name"] + "]"
            key_word += t_config["user_id"]
        else:
            key_word += t_config["user_id"]

        if t_config["time_range"]["enable"]:
            start_time = t_config["time_range"]["start_time"]
            stop_time = t_config["time_range"]["stop_time"]
            if user_Chinese_symbols and isinstance(start_time, str):
                start_time = start_time.replace(":", "：")
            if user_Chinese_symbols and isinstance(stop_time, str):
                stop_time = stop_time.replace(":", "：")
            if not stop_time:
                stop_time = "x"
            if not start_time:
                start_time = "x"
            key_word += "[{} - {}]".format(start_time, stop_time)


    elif config["mode"] == 2:
        t_config = config["search_config"]
        key_word = "wb_2_{}".format(t_config["search_code"])

    elif config["mode"] == 3:
        t_config = config["single_weibo_with_comment_real-time_updates_config"]
        re_tid = re.search(r"weibo.com/(.*?/.*?)\?", t_config["weibo_url"])
        key_word = "wb_3_{}".format(re_tid.group(1))
    else:
        print("你咋没调check_config")
        exit()
    return key_word


if not check_config():
    print("配置文件错误，按任意键退出")
    ord(msvcrt.getch())
    exit()
else:
    print("检查完成")
FEED_EXPORT_ENCODING = "gbk"

# 指定Redis的主机名和端口
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

# redis_key = "test"
# SCHEDULER_DUPEFILTER_KEY = redis_key

# redis key
redis_key = get_key_word(False)
SCHEDULER_DUPEFILTER_KEY = '{}:dupefilter'.format(redis_key)
SCHEDULER_QUEUE_KEY = "{}:requests".format(redis_key)

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# DUPEFILTER_CLASS = "scrapy_redis_bloomfilter.dupefilter.BaseDupeFilter"
DUPEFILTER_CLASS = "T_filter.Filtre1.RFPDupeFilter"

# 将Requests队列持久化到Redis，可支持暂停或重启爬虫
SCHEDULER_PERSIST = True
# Requests的调度策略，默认优先级队列
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

RETRY_TIMES = 4
LOG_FILE = log_path

BOT_NAME = 'scrapy_weiboSpider'
SPIDER_MODULES = ['scrapy_weiboSpider.spiders']
NEWSPIDER_MODULE = 'scrapy_weiboSpider.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 12

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    # "cookie": "SINAGLOBAL=9660189142619.871.1625547924755; wvr=6; wb_timefeed_1748134632=1; wb_view_log_1748134632=1536*8641.375; SCF=AsWBxcEA8_DLTQ5GjR5LrGewVJ8Q3NfoF0k7jCICNDnB91oHbBB6fLHwSIvcfTKkQA3A1w8rt8y2DVJJos6NWiU.; SUB=_2A25N9tUiDeRhGedJ71oQ8yrKyD6IHXVugkHqrDV8PUNbmtANLRDlkW9NUeseWhMCLTKzAhgg2vcUZS_eNmNFw-oN; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFlK8wHn55LiDCvTD8mF1.n5JpX5KzhUgL.Fo2NShnpe0Bce0z2dJLoIpXXeCH8SC-RxbHFSEH8SE-RBEHWBbH8SE-RBEHWBntt; ALF=1658050801; SSOLoginState=1626514802; _s_tentry=login.sina.com.cn; UOR=,,login.sina.com.cn; Apache=125674319378.62584.1626514803278; ULV=1626514803286:29:29:16:125674319378.62584.1626514803278:1626513787253; webim_unReadCount=%7B%22time%22%3A1626518638626%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A2%7D"
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    'scrapy_weiboSpider.middlewares.ScrapyWeibospiderSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy_weiboSpider.middlewares.ScrapyWeibospiderDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'scrapy_weiboSpider.pipelines.ScrapyWeibospiderPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
