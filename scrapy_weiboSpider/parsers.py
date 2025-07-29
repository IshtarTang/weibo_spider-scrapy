from scrapy_weiboSpider.items import weiboItem, commentItem
import logging
import time
from lxml.html import etree
from datetime import datetime
from scrapy_weiboSpider import fetcher
from scrapy_weiboSpider.utils.log_print_utils import log_and_print


def parse_wb(wb_data: dict,
             config, cookies, blog_headers, comm_headers,
             parse_comms_callback, get_single_wb_callback, get_long_text_callback
             ):
    """
    微博内容完全解析
    制作weibo信息item，根据配置构建评论、源微博请求

    刚从spider那边拆过来，还有一些要修的，有兴致再说
    callback那一堆应该可以弄成可以选，可能会有一些只需要 item的场景
    对conifg的依赖感觉也可以修一下，默认只传当前微博要的评论数，源微博的获取评论数弄成可选变量


    :param wb_data: 任何一种响应里微博信息部分
    :param config: 配置文件
    :param cookies:
    :param blog_headers: 博客接口请求头
    :param comm_headers: 评论接口请求头
    :param parse_comms_callback:
    :param get_single_wb_callback:
    :return:第一个yield状态（跳过这条/获取失败/获取成功），获取成功的话后面继续yield item或request，其它状态则没有后续yield
    """
    get_rwb_detail = config["get_rwb_detail"]

    wb_item = extract_wb_item(wb_data)
    if not wb_item:
        # 没获取到bid才会返回空，说明这条微博完全获取不到
        yield None
        return

    # 没有什么异常，返回ok状态码
    yield "ok"

    user_id = wb_item["user_id"]
    comm_config = config["get_comm_num"]
    if user_id == config["user_id"]:
        rcomm_target = comm_config["wb_rcomm"]
        ccomm_target = comm_config["wb_ccomm"]
    else:
        rcomm_target = comm_config["rwb_rcomm"]
        ccomm_target = comm_config["rwb_ccomm"]

    # 获取评论
    first_comm_request = fetcher.build_firse_rcomment_request(
        wb_data, rcomm_target, ccomm_target,
        parse_comms_callback, cookies, headers=comm_headers)
    if first_comm_request:
        yield first_comm_request

    # 做字数判断，过长的要单独一个请求获取完整内容
    text_len = wb_data.get("textLength", 0)
    # 字数超过的送到获取长文的地方去，原content会被覆盖
    if text_len >= 240:
        yield fetcher.build_long_text_request(wb_item, get_long_text_callback, cookies=cookies,
                                              blog_headers=blog_headers)
    else:
        message = "{} 解析完毕:{}".format(wb_item["wb_url"], wb_item["content"][:10].replace("\n", "\t"))
        log_and_print(message, "debug")
        yield wb_item

    # 处理源微博
    r_href = wb_item["r_href"]
    if r_href:
        r_wb_url = "https://weibo.com" + r_href
        if get_rwb_detail:  # 获取源微博详情
            print("{}的源微博为 {}，准备进行详细解析".format(wb_item["wb_url"], r_wb_url))
            yield fetcher.build_single_wb_request(
                r_href.split("/")[-1], get_single_wb_callback, cookies, blog_headers,
                retweeted_status=wb_data.get("retweeted_status", None))
        else:  # 源微博只简单解析
            print("{}的源微博为 {}，准备进行simple parse".format(wb_item["wb_url"], r_wb_url))
            wb_item["remark"] += "设置为不获取详细源微博"
            r_wb_item = extract_wb_item(wb_data["retweeted_status"])
            yield r_wb_item


def extract_wb_item(wb_data, wb_item=None):
    """
    从wb_data里提取需要的信息制作item
    :param wb_data:响应数据中一条微博的json，可以是完整数据也可以是retweeted_status
    :param wb_item:  已经在别的地方存了一些信息的 weiboItem
    :return:加了新解析出内容的weiboItem
    """
    if wb_item is None:
        wb_item = weiboItem()
        wb_item["remark"] = ""
    try:
        bid = wb_data["mblogid"]
        wb_item["bid"] = bid  # bid，微博的标识
        user_id = wb_data["user"]["idstr"]
        wb_item["user_id"] = user_id  # 用户id
    except:
        # bid和用户id获取不到说明这条微博完全无法看到
        logging.warning(f"{time.time()} 出现完全无法解析的微博，上阶段信息{wb_data}")
        return None

    wb_item["wb_url"] = "https://weibo.com/{}/{}".format(wb_item["user_id"], wb_item["bid"])
    wb_item["user_name"] = wb_data["user"]["screen_name"]  # 用户名
    html_text = wb_data["text_raw"]  # 微博正文
    content_parse = etree.HTML(html_text)
    content = "\n".join(content_parse.xpath("//text()"))
    wb_item["content"] = content  # 微博正文

    created_at = wb_data["created_at"]
    create_datetime = datetime.strptime(created_at, '%a %b %d %X %z %Y')
    create_time = datetime.strftime(create_datetime, "%Y-%m-%d %H:%M")
    wb_item["public_time"] = create_time  # 发表时间

    wb_item["public_timestamp"] = int(time.mktime(create_datetime.timetuple()) * 1000)  # 发表时间的时间戳
    wb_item["share_scope"] = str(wb_data["visible"]["type"])  # 可见范围
    wb_item["like_num"] = wb_data["attitudes_count"]  # 点赞数（含评论点赞）
    wb_item["forward_num"] = wb_data["reposts_count"]  # 转发数
    wb_item["comment_num"] = wb_data["comments_count"]  # 评论数
    wb_item["weibo_from"] = wb_data["source"]  # 微博来源

    mid = wb_data["mid"]  # 微博的数字编号，拿图片/评论会用到
    # 获取图片
    img_list = []
    pic_ids = wb_data.get("pic_ids", [])
    wimg_url_base = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}"

    for pid in pic_ids:
        wimg_url = wimg_url_base.format(user_id, mid, pid)
        img_list.append(wimg_url)
    wb_item["img_list"] = img_list  # 图片

    # 链接
    links = []
    if wb_data.get("url_struct", []):
        for url_info in wb_data["url_struct"]:
            links.append(url_info["ori_url"])
    wb_item["links"] = links

    retweeted_status = wb_data.get("retweeted_status", 0)
    wb_item["is_original"] = 0 if retweeted_status else 1  # 是否原创
    r_href = ""
    if not wb_item["is_original"]:  # 不是原创微博时，解析源微博信息
        r_bid = ""
        r_user = ""
        try:
            r_bid = wb_data["retweeted_status"].get("mblogid", "")  # 源微博bid
            r_user = wb_data["retweeted_status"].get("user", {}).get("idstr", "")  # 源微博用户id
        except:
            wb_item["remark"] += "无法获取源微博"
        if r_bid and r_user:  # 这两都有说明源微博可见
            r_href = "/{}/{}".format(r_user, r_bid)
    wb_item["r_href"] = r_href

    # 有兴致的话可能会添上吧
    wb_item["t_bid"] = ""
    wb_item["r_weibo"] = {}
    wb_item["video_url"] = ""
    wb_item["article_url"] = ""
    wb_item["article_content"] = ""

    return wb_item


def extract_comm_item(comm_data: dict, superior_id, comm_type):
    """
    解析评论，把需要的字段做成item，以及构建子评论请求
    :param comm_data: 薅来的评论信息
    :param superior_id: 上级的id
    :param comm_type: 评论类型，root或child
    """
    comm_item = commentItem()
    comm_item["comment_type"] = comm_type
    comm_item["superior_id"] = superior_id
    comment_id = comm_data["idstr"]
    comm_item["comment_id"] = comment_id
    content_parse = etree.HTML(comm_data["text"])
    content = " ".join(content_parse.xpath("//text()"))
    comm_item["content"] = content
    comm_item["user_name"] = comm_data["user"]["screen_name"]
    comm_item["user_url"] = "https://weibo.com" + comm_data["user"]["profile_url"]
    created_at = comm_data["created_at"]
    create_datetime = datetime.strptime(created_at, '%a %b %d %X %z %Y')
    create_time = datetime.strftime(create_datetime, "%Y-%m-%d %H:%M")
    comm_item["date"] = create_time
    try:
        comm_item["like_num"] = comm_data["like_counts"]
    except KeyError:
        comm_item["like_num"] = -1
        logging.warning(f"点赞解析失败，设为-1，上级id {superior_id},类型 {comm_type}，当前comm {comm_data}")
    comm_item["img_url"] = ""

    links = []
    if comm_data.get("url_struct", []):
        links_info = comm_data["url_struct"]
        for link_info in links_info:
            link = link_info.get("ori_url", "")
            if not link:
                link = link_info.get("long_url", "")
            links.append(link)
            if not link:
                logging.warning(f"评论配图解析失败，上级id {superior_id},类型 {comm_type}，当前comm {comm_data}")

    comm_item["link"] = links

    return comm_item
