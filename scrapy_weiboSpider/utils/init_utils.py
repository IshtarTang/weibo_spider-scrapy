import time
import msvcrt
import logging
import re
import redis
from scrapy_weiboSpider.utils import file_utils, time_utils, config_utils
from scrapy_weiboSpider.utils.log_print_utils import log_and_print


def has_pending_requests_in_redis(settings):
    """
    :param settings: scrapy的setting
    :return:  redis中有没有上次没运行完的请求
    """
    continue_previous_run = 0
    redis_host = settings.get("REDIS_HOST", '127.0.0.1')
    redis_port = settings.getint("REDIS_PORT", 6379)
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    redis_requests_key = settings.get("SCHEDULER_QUEUE_KEY", "")
    if r.zcard(redis_requests_key) > 0:
        continue_previous_run = 1
    return continue_previous_run


def get_wb_time_start_limit(time_limit_config, result_filepath):
    """

    :param time_limit_config: config["get_comm_num"]
    :param result_filepath: （上次运行）结果文件路径
    :return:
    """
    if time_limit_config == "auto":  # 自动模式，读取之前获取的最后一条微博时间，此前的微博不再次获取
        wb_time_start_limit = file_utils.get_last_wb_public_time(file_utils.get_result_wb_filepath(result_filepath))
    elif time_limit_config == "auto2":  # auto2模式是按已保存过的bid判断的，不做时间限制
        wb_time_start_limit = 0
    elif isinstance(time_limit_config, str):  # 手动模式，yyyy-mm-dd hh:MM格式
        if re.search(r"[12]\d\d\d-[012]\d-[0123]\d [012]\d:[012345]\d", time_limit_config):
            wb_time_start_limit = time_utils.to_millis_timestamp(time_limit_config)
        else:
            wb_time_start_limit = 0
    elif isinstance(time_limit_config, int):  # 手动模式，时间戳/毫秒级时间戳
        wb_time_start_limit = time_utils.to_millis_timestamp(time_limit_config)
    else:
        wb_time_start_limit = 0
    return wb_time_start_limit


def init_print(config, saved_main_bid, result_filepath, time_start_limit):
    """
    一些打印输出
    """
    # 上次的记录
    if saved_main_bid:
        log_and_print(
            f"\n录入 {result_filepath} 的微博数据\n读取到上次运行保存的微博{len(saved_main_bid)}条")
    else:
        log_and_print(f"\n{result_filepath} 为空，无上次运行记录")
    # key
    key_word = config_utils.get_key_word(config)
    print("\n本次运行的文件key为 {}".format(key_word))
    # 评论设置
    comm_config_str = {"wb_rcomm": "微博根评论", "wb_ccomm": "微博子评论", "rwb_rcomm": "源微博根评论",
                       "rwb_ccomm": "源微博子评论"}
    print("评论获取设置：")
    for comm_config in config["get_comm_num"]:
        get_comm_num = config["get_comm_num"][comm_config]
        print("    {}:{}".format(comm_config_str[comm_config],
                                 get_comm_num if get_comm_num != -1 else "all"))

    # 时间限制设置
    time_limit_config = config["time_limit"]
    message = ""
    if time_limit_config:
        print("时间限制设定为", time_limit_config)

        if time_limit_config == "auto" and time_start_limit:
            message = f"已启动自动时间限制，本次将获取 now - {time_utils.to_datetime(time_start_limit)} 的微博到文件中"
        elif time_limit_config == "auto":
            message = "已启动自动时间限制，未检查到记录文件，将获取所有微博"
        elif time_limit_config == "auto2":
            message = f"已启用auto2模式，本次将获取未在文件中的微博"
        elif time_start_limit:
            message = f"已启动手动时间限制，本次将获取 now - {time_limit_config} 的微博到文件中"
        else:
            message = f"配置项 时间限制 {time_limit_config} 无效"
    log_and_print(message)


def confirm_start(ensure_ask):
    if ensure_ask:
        print("请确认redis已启动，按任意键继续，或Esc以退出")
        x = ord(msvcrt.getch())
        if x == 27:
            print("程序退出")
            logging.info("主动退出")
            import sys
            sys.exit(0)
