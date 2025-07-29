import re

import scrapy.http
from scrapy import Request
import logging
import json


def build_mainpage_turning_request(response: scrapy.http.Response, user_id, callback, cookies, headers):
    # 翻页

    page = int(response.request.url.split("page=")[1].split("&")[0])
    j_data = json.loads(response.text)

    since_id = j_data["data"]["since_id"]
    if since_id:  # 有下一页
        # 把下一页的链接送进去
        next_url = "https://weibo.com/ajax/statuses/mymblog?" \
                   "uid={}&page={}&feature=0&since_id={}".format(user_id, page + 1, since_id)
        return Request(next_url, callback=callback,
                       meta={"ok1_retry": 0,
                             "json_field_retry": [["data", "list"]],
                             "json_field_retry_allow_empty": True},
                       dont_filter=True, cookies=cookies, headers=headers)
    else:  # 有时候会出现页面有内容但没有翻页id的情况 ，把翻页id作为必要响应内容扔回去重新请求
        new_request = response.request.copy()
        new_request.meta["json_field_retry"] = [["data", "since_id"]]
        new_request.meta["no_sinceId_retry"] = 1  # 设了这个之后就不会再解析一次该页的微博内容
        return new_request


def build_firse_rcomment_request(wb_data, rcomm_target, ccomm_target,
                                 parse_comm_callback, cookies, headers):
    """
    偷懒用，真正的逻辑看最后return那个函数
    :param wb_data: mymblog的响应内容，json格式
    :return:
    """
    total_comments = wb_data["comments_count"]
    bid = wb_data["mblogid"]
    mid = wb_data["mid"]
    blog_user_id = wb_data["user"]["idstr"]
    return build_firse_rcomment_request_(total_comments, rcomm_target, ccomm_target,
                                         bid, mid, blog_user_id,
                                         parse_comm_callback, cookies, headers)


def build_firse_rcomment_request_(total_comments, rcomm_target, ccomm_target,
                                  bid, mid, blog_user_id,
                                  callback, cookies, headers):
    """
    需要时构建评论请求并返回，不需要时返回None
    :param total_comments:  该条微博的评论数量
    :param bid: 博文唯一标识
    :param mid: 博文的一串数字id
    :param blog_user_id: 发布这条微博用户的id
    :param callback: scrapy.Request 的 callback
    :return: 该条微博有评论且设置了需要爬，返回构建的Request，否则返回None
    """
    # 当前微博是否有评论
    if total_comments == 0:
        message = ""
        return None

    if rcomm_target == 0:
        message = ""
        return None
    # 构建请求
    comm_url_base = "https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&" \
                    "id={}&is_show_bulletin=2&is_mix=0&count=10&uid={}"
    comm_url = comm_url_base.format(mid, blog_user_id)

    return Request(
        comm_url, callback=callback,
        meta={"superior_id": bid, "blog_user_id": blog_user_id, "comm_type": "root", "comm_fetched": 0,
              "rcomm_target": rcomm_target, "ccomm_target": ccomm_target,
              "ok1_retry": 0},
        cookies=cookies, headers=headers,
        dont_filter=False)  # 这里是会去重的，单次运行时每条微博的评论只获取一次


def build_firse_ccomment_request(
        superior_id, blog_user_id, rcomm_target, ccomm_target,
        parse_comms_callback, comm_headers, cookies):
    ccomm_url = "https://weibo.com/ajax/statuses/buildComments?is_reload=1&" \
                "id={}&is_show_bulletin=2&is_mix=1&fetch_level=1&count=20&" \
                "uid={}&max_id=0".format(superior_id, blog_user_id)
    return Request(
        ccomm_url, callback=parse_comms_callback,
        meta={"superior_id": superior_id, "blog_user_id": blog_user_id, "comm_type": "child",
              "rcomm_target": rcomm_target, "ccomm_target": ccomm_target,
              "comm_fetched": 0, "ok1_retry": 0},
        headers=comm_headers, cookies=cookies, dont_filter=True)


def build_comment_turning_request(response: scrapy.http.Response, cookies, headers, parse_comm_callback):
    """
    根据配置判断是否要继续翻页，构建评论翻页请求，root评论和child评论都可以
    :return:
    """
    j_data = json.loads(response.text)
    o_url = response.request.url
    meta = response.meta.copy()

    superior_id = meta["superior_id"]  # 上级的id
    blog_user_id = meta["blog_user_id"]  # 用户id
    comm_type = meta["comm_type"]  # 评论类型
    comm_fetched = meta["comm_fetched"]  # 评论计数

    comms = j_data["data"]  # 获取到的评论数据，是个list，一条一个评论
    max_id = j_data["max_id"]  # max_id用于获取下一页评论

    # 确定评论限制多少数量
    rcomm_target = meta["rcomm_target"]
    ccomm_target = meta["ccomm_target"]
    if comm_type == "root":
        comm_limit = rcomm_target
    else:
        comm_limit = ccomm_target

    if not max_id:  # 没有max_id说明没有下一页
        yield "no_max_id", ""
        return
    if comm_fetched >= comm_limit:  # 到达限制数量
        yield "comm_limit", f"{comm_fetched}/{comm_limit}"
        return

    # 把新的max_id换进去就是下一页的链接
    if "max_id" in o_url:
        next_url = re.sub("&max_id=\d+", f"&max_id={max_id}", o_url)
    else:
        next_url = o_url + f"&max_id={max_id}"
    next_meta = {"superior_id": superior_id, "blog_user_id": blog_user_id, "comm_type": comm_type,
                 "rcomm_target": rcomm_target, "ccomm_target": ccomm_target,

                 "comm_fetched": comm_fetched, "ok1_retry": 0}

    # 直接创建新链接 而不使用旧链接来替换，但是要用到上级id
    # 代码和文件里root评论的superior_id都是bid,但是获取评论要的是mid，感觉会混淆
    # if comm_type == "root":
    #     rcomm_url_base = "https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&" \
    #                      "id={}&is_show_bulletin=2&is_mix=0&count=20&uid={}&max_id={}"
    #     next_url = rcomm_url_base.format(superior_id_in_comm_url, user_id, max_id)
    # else:
    #     ccomm_url_base = "https://weibo.com/ajax/statuses/buildComments?is_reload=1&" \
    #                      "id={}&is_show_bulletin=2&is_mix=1&fetch_level=1&count=20&" \
    #                      "uid={}&max_id={}"
    #     next_url = ccomm_url_base.format(superior_id_in_comm_url, user_id, max_id)

    # 一些异常情况
    if len(comms) == 0:
        # 评论显示被限制的情况，能一直翻但实际上不会返回新评论，停止继续翻
        trends_text = j_data["trendsText"]
        if trends_text in ["博主已开启评论精选", "博主已开启防火墙，部分内容暂不展示", "已过滤部分评论",
                           "由于博主设置，部分评论暂不展示"]:
            message = f"{superior_id} 下 {comm_type} 状态： {trends_text}，结束获取该条微博评论"
            logging.debug(message)
            print(message)
            yield f"wb limit", f"{trends_text}"
            return
        elif trends_text == "已加载全部评论" and comm_type == "root":
            # 一种很迷惑的情况，需要点[加载更多]15次才能获取到下一页数据(一个例子 NFsyODei3)
            # 出现这种情况就开始在meta计数，如果计到16还获取不到就放弃
            # “已加载全部评论”是微博默认trends_text，就算后面还有评论也显示这个。
            # 所以这里其实是默认root评论在本页获取到0条时翻15次
            failure_with_max_id = meta.get("failure_with_max_id", 0)
            next_meta["failure_with_max_id"] = failure_with_max_id + 1
            if failure_with_max_id >= 16:
                yield "15_done", ""
                return
        else:
            yield f"unknown trendsText", f"{j_data['trendsText']}"
            return
    yield f"ok", f"{comm_fetched}/{comm_limit}"
    yield Request(next_url, callback=parse_comm_callback, priority=15,  # 这里用了高优先级
                  meta=next_meta, dont_filter=True, cookies=cookies, headers=headers, )


def build_long_text_request(wb_item, long_text_callback, cookies, blog_headers):
    longtext_url = "https://weibo.com/ajax/statuses/longtext?id={}".format(wb_item["bid"])
    return Request(longtext_url, callback=long_text_callback,
                   cookies=cookies, headers=blog_headers,
                   meta={"wb_item": wb_item, "count": 0, "ok1_retry": 0}, dont_filter=True)


def build_single_wb_request(bid, get_single_wb_callback, cookies, blog_headers, retweeted_status=None):
    r_info_url = "https://weibo.com/ajax/statuses/show?id=" + bid
    return Request(r_info_url, callback=get_single_wb_callback,
                   cookies=cookies, headers=blog_headers,
                   meta={"count": 0, "retweeted_status": retweeted_status},
                   dont_filter=False)
