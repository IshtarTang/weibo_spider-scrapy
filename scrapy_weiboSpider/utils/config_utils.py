import time
import os
import re

from scrapy_weiboSpider.utils import time_utils
import json

"""
与配置文件有关的工具

"""


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as op:
        config_str = op.read()
    config = json.loads(config_str)
    return config


def cookiestoDic(str1):
    """
    chrome上复制下来的cookeis转dict
    :param str1:
    :return:
    """
    result = {}
    cookies = str1.split(";")
    cookies_pattern = re.compile("(.*?)=(.*)")

    for cook in cookies:
        cook = cook.replace(" ", "")
        header_name = cookies_pattern.search(cook).group(1)
        header_value = (cookies_pattern.search(cook).group(2))
        result[header_name] = header_value

    return result


def get_log_path(key_word="", log_dir="log"):
    """
    该配置文件的日志路劲
    :return:
    """
    date1 = time.strftime("%m%d", time.localtime())
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if key_word:
        ident = f"{key_word}_{date1}"
    else:
        ident = date1
    n = 1
    while True:
        log_path = os.path.join(log_dir, f"{ident}_{n}.log")
        if not os.path.exists(log_path):
            return log_path
        else:
            n += 1


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
            if (start_time and stop_time) and not time_utils.is_a_early_than_b(start_time, stop_time, False):
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
        mode_id = config["id"]
        print("没有序号为{}的模式".format(mode_id))
        return False

    return True


def get_key_word(config, user_Chinese_symbols=True):
    """
    通过配置文件生成一个标识符，用于redis key和结果文件名
    :param user_Chinese_symbols:将时间设置中英文":"符替换为中文"："
    :return:
    """
    key_word = ""
    if config["id"] == 1:
        if config["user_name"]:
            key_word += "[" + config["user_name"] + "]"
            key_word += config["user_id"]
        else:
            key_word += config["user_id"]
        if config.get("time_range", {}).get("enable", {}):
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
        if config.get("debug", {}).get("on", {}):
            key_word = "[debug]" + key_word
    elif config["id"] == 2:
        config = config["search_config"]
        key_word = "wb_2_{}".format(config["search_code"])

    elif config["id"] == 3:
        config = config["single_weibo_with_comment_real-time_updates_config"]
        re_tid = re.search(r"weibo.com/(.*?/.*?)\?", config["weibo_url"])
        key_word = "wb_3_{}".format(re_tid.group(1))
    else:
        print("你咋没调check_config")
        exit()
    return key_word


def get_result_filepath(config):
    """
    该配置的结果文件路劲
    :param config:
    :return:
    """
    key_word = get_key_word(config)
    dir_path = config.get("dir_path", "file")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    path = os.path.join(dir_path, key_word)
    return path
