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


def check_config(config):
    """
    配置文件检查
    :return:
    """
    print("检查配置文件")
    # 个人主页模式
    if config["id"] == 1:
        print("保存个人主页模式")
        if not config["user_id"]:
            print("id 为空")
            return False
        # 评论数设置检查
        if config.get("get_comm_num", None):
            comm_configs = config["get_comm_num"]
            for comm_config in ["wb_rcomm", "wb_ccomm", "rwb_rcomm", "rwb_ccomm"]:
                if comm_configs.get(comm_config, None) == None:
                    print("配置项 {} 缺失，程序退出".format(comm_config))
                    return False
                if not isinstance(comm_configs[comm_config], int, ):
                    print("配置项 {} 应为int类型，程序退出".format(comm_config))
                    return False
        else:
            print("配置项 get_comm_num 缺失，程序退出")
            return False

        # 时间范围功能参数检查
        if config["time_range"]["enable"]:
            start_time = config["time_range"]["start_time"]
            stop_time = config["time_range"]["stop_time"]
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
    elif config["id"] == 2:
        print("搜索模式")
        config = config["search_config"]
        if not config["search_code"]:
            print("搜索关键词不能为空")
            return False
        print("这个模式的功能还没开始写")
        return False

    # 评论实时更新模式参数检查
    elif config["id"] == 3:
        print("评论实时抓取模式")
        config = config["single_weibo_with_comment_real-time_updates_config"]
        if not config["weibo_url"]:
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


def get_key_word(config, user_Chinese_symbols=True):
    """
    通过配置文件生成存到redis中key的名字
    :param user_Chinese_symbols:将时间设置中英文":"符替换为中文"："
    :return:
    """
    key_word = ""
    if config["mode"] == 1:
        key_word = ""
        if config["user_name"]:
            key_word += "[" + config["user_name"] + "]"
            key_word += config["user_id"]
        else:
            key_word += config["user_id"]

        if config["time_range"]["enable"]:
            start_time = config["time_range"]["start_time"]
            stop_time = config["time_range"]["stop_time"]
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
        config = config["search_config"]
        key_word = "wb_2_{}".format(config["search_code"])

    elif config["mode"] == 3:
        config = config["single_weibo_with_comment_real-time_updates_config"]
        re_tid = re.search(r"weibo.com/(.*?/.*?)\?", config["weibo_url"])
        key_word = "wb_3_{}".format(re_tid.group(1))
    else:
        print("你咋没调check_config")
        exit()
    return key_word


config = json.load(open(config_path, "r", encoding="utf-8"))

if not check_config(config):
    print("配置文件错误，按任意键退出")
    ord(msvcrt.getch())
    exit()
else:
    print("检查完成")
FEED_EXPORT_ENCODING = "gbk"

# 指定Redis的主机名和端口
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379

# redis key
# redis_key = "test"
redis_key = get_key_word(config, False)
SCHEDULER_DUPEFILTER_KEY = '{}:dupefilter'.format(redis_key)
SCHEDULER_QUEUE_KEY = "{}:requests".format(redis_key)

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
DUPEFILTER_CLASS = "T_filter.Filtre1.RFPDupeFilter"

# 将Requests队列持久化到Redis，可支持暂停或重启爬虫
SCHEDULER_PERSIST = True
# Requests的调度策略，默认优先级队列
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

RETRY_TIMES = 4
LOG_FILE = get_log_path()
LOG_LEVEL = 'DEBUG'

BOT_NAME = 'scrapy_weiboSpider'
SPIDER_MODULES = ['scrapy_weiboSpider.spiders']
NEWSPIDER_MODULE = 'scrapy_weiboSpider.spiders'

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 20
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16


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
