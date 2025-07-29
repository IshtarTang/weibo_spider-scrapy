from scrapy_weiboSpider.utils import time_utils
from datetime import datetime


def mainpage_wb_filter(wb_data, main_user_id, time_limit_conifg="", wb_time_start_limit=None, saved_all_bid=None):
    # 时间限制功能
    user_id = wb_data.get("user", {}).get("idstr", "")
    if wb_time_start_limit and user_id == main_user_id:
        created_at = wb_data.get("created_at", "Thu Jan 01 00:00:00 +0000 1970")
        if time_utils.is_a_early_than_b(created_at, wb_time_start_limit):
            return True, f"time limit:{created_at}"  # 该微博不在指定时间范围内,返回 状态:该微博的创建时间

    # auto2模式
    bid = wb_data.get('mblogid', "")
    if time_limit_conifg == "auto2":
        if bid in saved_all_bid:
            return True, f"auto2 limit:{bid}"  # auto2 limit不重复保存微博,该微博已在文件中,返回 状态:该微博bid

    # 过滤掉主页的点赞
    if "赞过" in wb_data.get("title", {}).get("text", ""):
        return True, "filter like"

    return False, ""


def mainpage_wb_timelimit():
    time_limit_reached = ""


def mainpage_debug_page_limit(debug_config, current_page):
    """
    debug的页数限制功能是否生效（会在该页阻止继续翻页）
    :param debug_config:
    :param current_page:
    :return: 不生效返回0，生效返回限制的页数
    """
    if debug_config.get("on", {}):
        page_limit = debug_config.get("page_limit", -1)
        if page_limit != -1 and current_page > page_limit:
            return page_limit
    return 0


def mainpage_stop_by_timelimit(wbs_info, time_start_limit):
    """
    :param wbs_info: 一页用户主页的微博
    :param time_start_limit: 时间限制设定
    :return: 是否所有微博都早于设定的时间,提示信息
    """
    if time_start_limit != 0:
        # 找当前页最新一条微博
        newest_wb_create_at = max([datetime.strptime(
            weibo_info.get("created_at", "Thu Jan 01 00:00:00 +0000 1970"), '%a %b %d %X %z %Y').timestamp()
                                   for weibo_info in wbs_info])
        # 如果本页最新一条比限制时间早，直接截断
        if time_utils.is_a_early_than_b(newest_wb_create_at, time_start_limit):
            message = ("time limit：仅获取 {} 之后发布的微博，当前最页面新微博时间{}，用户主页获取结束"
                       .format(time_utils.to_datetime(time_start_limit),
                               time_utils.to_datetime(newest_wb_create_at)))
            return True, message
        else:
            return False, ""
    return False, ""


def should_get_child_comm(comm_config, comm_type, user_id, main_user_id):
    """
    是否获取某一评论的子评论
    :param comm_config: 评论配置
    :param comm_type: 评论类型
    :param user_id: 该条评论所属微博博主id
    :param main_user_id: 目标用户id
    :return:
    """
    if comm_type == "root":
        if user_id == main_user_id:
            return comm_config["wb_ccomm"]
        else:
            return comm_config["rwb_ccomm"]
    else:
        return 0
