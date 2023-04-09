# -*- coding: utf-8 -*-
import scrapy
import os
from datetime import datetime
import json
import time
import sys
from lxml.html import etree
from scrapy import Request
import msvcrt
import logging
from scrapy_weiboSpider.items import weiboItem, commentItem
from gadget import comm_tool


class WeiboSpiderSpider(scrapy.Spider):
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy_weiboSpider.middlewares.ScrapyWeibospiderDownloaderMiddleware': 543,
            'scrapy_weiboSpider.middlewares.MyCountDownloaderMiddleware': 552,  # 比RetryMiddleware早一点
        }
    }
    name = 'new_wb_spider'
    allowed_domains = ['weibo.com']

    from scrapy_weiboSpider.config_path_file import config_path
    config = json.load(open(config_path, "r", encoding="utf-8"))
    user_id = config["user_id"]
    key_word = comm_tool.get_key_word(config)
    saved_key = []
    blog_headers = {
        'authority': 'weibo.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'client-version': 'v2.37.17',
        'pragma': 'no-cache',
        'referer': 'https://weibo.com/u/{}'.format(config["user_id"]),
        'sec-ch-ua': '^\\^Chromium^\\^;v=^\\^106^\\^, ^\\^Google',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '^\\^Windows^\\^',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'server-version': 'v2022.12.21.1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    comm_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
    }

    cookies = comm_tool.cookiestoDic(config["cookies_str"])

    # 一点废稿，spider的部分成功用到指令路径了，但是setting和pipline中都需要用配置文件，没办法从指令读
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # 如果指令传了配置路径，优先使用指令指定的配置文件
    #     if kwargs.get('config_path', ""):
    #         config_path = "./configs/" + kwargs.get('config_path')
    #         self.config = json.load(open(config_path, "r", encoding="utf-8"))
    #         print(f"从指令读取配置路径 {config_path}")
    #         logging.info(f"从指令读取配置路径 {config_path}")
    #     else:
    #         # 读文件设置的
    #         from scrapy_weiboSpider.config_path_file import config_path
    #         self.config = json.load(open(config_path, "r", encoding="utf-8"))
    #         print(f"从文件读取配置路径 {config_path}")
    #         logging.info(f"从文件读取配置路径 {config_path}")

    def start(self):
        """
        一些打印输出；读上次获取完成的微博，制成self.saved_key
        """
        print("\n本次运行的文件key为 {}".format(self.key_word))
        comm_config_str = {"wb_rcomm": "微博根评论", "wb_ccomm": "微博子评论", "rwb_rcomm": "源微博根评论", "rwb_ccomm": "源微博子评论"}
        print("评论获取设置：")
        for comm_config in self.config["get_comm_num"]:
            get_comm_num = self.config["get_comm_num"][comm_config]
            print("    {}:{}".format(comm_config_str[comm_config],
                                     get_comm_num if get_comm_num != -1 else "all"))

        # 录入之前的下载记录，避免重复爬取
        per_wb_path = "./file" + "/" + self.key_word + "/prefile/weibo.txt"
        saved_key_config = self.config.get("deubg", {}).get("saved_key_file", "")
        ########################
        # 在这里加扫描记录功能
        if os.path.exists(per_wb_path):
            if "pwb" in saved_key_config or not saved_key_config:
                file1 = open(per_wb_path, "r", encoding="utf-8").read().strip()
                if file1:
                    tmp_str = "[" + ",".join(file1.split("\n")) + "]"
                    file = json.loads(tmp_str, encoding="utf-8")
                    for x in file:
                        self.saved_key.append(x["bid"])
                    print("录入 {} 的微博下载记录".format(per_wb_path))
                else:
                    print("{} 无记录".format(per_wb_path))

        self.saved_key = list(set(self.saved_key))
        if self.saved_key:
            print("读取到上次运行保存的微博{}条".format(len(self.saved_key)))
        else:
            print("未读取到上次的记录")

        print("请确认redis已启动，按任意键继续，或Esc以退出")
        if not self.saved_key:
            x = ord(msvcrt.getch())
            if x == 27:
                print("程序退出")
                logging.info("主动退出")
                os._exit(0)

    def start_requests(self):
        self.start()
        start_url = "https://weibo.com/ajax/statuses/mymblog?" \
                    "uid={}&page={}&feature=0".format(self.user_id, 1)
        yield Request(start_url, callback=self.del_mymblog,
                      cookies=self.cookies, headers=self.blog_headers, meta={"my_count": 0},
                      dont_filter=True)

    def del_mymblog(self, response):
        """
        用户主页的数据
        """
        page = int(response.request.url.split("page=")[1].split("&")[0])
        print("已请求page {} 页面".format(page), end="\t")
        logging.info("已请求page {} ".format(page))

        # debug项，页数限制
        if self.config.get("debug", {}).get("on", {}):
            page_limt = self.config["debug"]["page_range"]
            if page_limt != -1 and page > page_limt:
                print(f"【debug项】 页数限制{page_limt}，结束获取")
                logging.info(f"【debug项】 页数限制{page_limt}，结束获取")
                return

        content = response.text
        j_data = json.loads(content)
        meta = response.meta
        # 下一页
        since_id = j_data["data"]["since_id"]
        if since_id:
            next_url = "https://weibo.com/ajax/statuses/mymblog?" \
                       "uid={}&page={}&feature=0&since_id={}".format(self.user_id, page + 1, since_id)
            yield Request(next_url, callback=self.del_mymblog, meta={"my_count": 0},
                          dont_filter=True, priority=1, cookies=self.cookies, headers=self.blog_headers)
        # 网络出问题时有可能获取不到下一页
        elif meta["my_count"] < 5:
            request = response.request
            request.meta["my_count"] += 1
            yield request
        else:
            print("页数{} 后面没了".format(page))

        # 是否正常获取到正文
        if not j_data.get("data", {}).get("list", []):
            if meta["my_count"] < 5:
                request = response.request
                request.meta["my_count"] += 1
                yield request
                logging.warning("page{} 无法获取到正文，尝试重新获取".format(page))
            else:
                logging.error("page{} 无法获取到正文，放弃".format(page))
                print("page{} 获取失败".format(page))
            return

        # 解析微博
        wb_list = j_data["data"]["list"]
        print("页面正常，本页共微博微博{}条，开始解析".format(page, len(wb_list)))
        # 循环微博，解析
        for wb_info in wb_list:
            item_and_request_generator = self.parse_wb(wb_info)
            for item_or_request in item_and_request_generator:
                yield item_or_request

    def get_comm(self, response):
        """
        root评论和child评论都走这个方法解析&翻页，用meta["comm_type"]区别
        user_id用于判断要爬多少条
        meta中必须有上级id superior_id 、 评论类型 comm_type 、用户id user_id、评论计数 comm_count
        :param response:
        :return:
        """
        content = response.text
        j_data = json.loads(content)
        meta = response.meta

        superior_id = meta["superior_id"]  # 上级的id
        user_id = meta["user_id"]  # 用户id
        comm_type = meta["comm_type"]  # 评论类型
        comm_count = meta["comm_count"]  # 评论计数

        comms = j_data["data"]  # 获取到的评论数据，是个list，一条一个评论
        comm_count += len(comms)
        max_id = j_data["max_id"]  # max_id用于获取下一页评论

        # 确定评论限制多少数量
        comm_limit = sys.maxsize
        comm_limit_config = self.config.get("get_comm_num", {})
        if comm_limit_config:
            # 是该用户的原创微博
            if str(self.config["user_id"]) == str(user_id):
                if comm_type == "root":  # 父评论
                    comm_limit = comm_limit_config["wb_rcomm"] if comm_limit_config["wb_rcomm"] != -1 else sys.maxsize
                else:  # 子评论
                    comm_limit = comm_limit_config["wb_ccomm"]
            # 被转发的微博
            else:
                if comm_type == "root":
                    comm_limit = comm_limit_config["rwb_rcomm"]
                else:
                    comm_limit = comm_limit_config["rwb_ccomm"]

        next_url = ""
        # 有max_id说明有下一页，如果没到限制的数量或者不限制（-1是不限制），把url改成下一页的继续爬
        if max_id and (comm_count < comm_limit or comm_limit == -1):
            o_url = response.request.url
            next_url = o_url.split("&max_id=")[0] + "&max_id=" + str(max_id)
            # 第一轮root评论的count是10，后面的和子评论的count都是20
            if "count=10" in next_url:
                next_url = next_url.replace("count=10", "count=20")
            yield Request(next_url, callback=self.get_comm,
                          meta={"superior_id": superior_id, "user_id": user_id, "comm_type": comm_type,
                                "comm_count": comm_count + len(comms), "my_count": 0},
                          dont_filter=True, cookies=self.cookies, headers=self.comm_headers, )
        if comm_count >= comm_limit and comm_limit != -1:
            logging.debug(
                "{}/{} {}已经获取足够评论条数 get {} limit{}".format(user_id, superior_id, response.url, comm_count, comm_limit))
        # 还没写，这里要处理能获取到下一页链接，但解析出的评论数量0的问题
        if len(comms) == 0 and next_url:
            logging.warning("评论 {} 未获取到内容，上级链接{}，类型{}，下个链接{}，当前内容 \n{}".
                            format(response.url, superior_id, comm_type, next_url,
                                   json.dumps(j_data, indent=4, ensure_ascii=False)))
            time.sleep(3)

        # 评论一条一条塞到解析方法里
        for comm in comms:
            commItem_and_rcommReqs = self.parse_comm(comm, superior_id, user_id, comm_type)
            for c_or_i in commItem_and_rcommReqs:
                yield c_or_i
        print("获取到{} comm {}条，上级为 {}".format(comm_type, len(comms), superior_id))
        logging.debug("获取到{} comm {}条，上级为 {}".format(comm_type, len(comms), superior_id))

    def get_single_wb(self, response):
        """
        单条微博正文解析
        :param response:
        :return:
        """
        content = response.text
        wb_info = json.loads(content, encoding="utf-8")
        item_and_request = self.parse_wb(wb_info)
        for i_or_r in item_and_request:
            yield i_or_r

    def parse_wb(self, wb_info: dict):
        """
        从响应的json里把需要的部分扣出来，做成item
        把评论请求搞出来
        :param wb_info:
        :return:
        """
        remark = ""
        wb_item = weiboItem()
        try:
            bid = wb_info["mblogid"]
        except:
            # bid获取不到说明这条微博完全无法看到
            return
        wb_item["bid"] = bid  # bid，微博的标识

        user_id = wb_info["user"]["idstr"]
        wb_item["user_id"] = user_id  # 用户id

        wb_item["wb_url"] = "https://weibo.com/{}/{}".format(wb_item["user_id"], wb_item["bid"])
        wb_item["user_name"] = wb_info["user"]["screen_name"]  # 用户名
        html_text = wb_info["text_raw"]  # html格式的微博正文
        content_parse = etree.HTML(html_text)
        content = "\n".join(content_parse.xpath("//text()"))
        wb_item["content"] = content  # 微博正文

        created_at = wb_info["created_at"]
        create_datetime = datetime.strptime(created_at, '%a %b %d %X %z %Y')
        create_time = datetime.strftime(create_datetime, "%Y-%m-%d %H:%M")
        wb_item["public_time"] = create_time  # 发表时间

        wb_item["public_timestamp"] = int(time.mktime(create_datetime.timetuple()) * 1000)  # 发表时间的时间戳
        wb_item["share_scope"] = str(wb_info["visible"]["type"])  # 可见范围
        wb_item["like_num"] = wb_info["attitudes_count"]  # 点赞数（含评论点赞）
        wb_item["forward_num"] = wb_info["reposts_count"]  # 转发数
        wb_item["comment_num"] = wb_info["comments_count"]  # 评论数
        share_repost_type = wb_info["share_repost_type"]
        wb_item["is_original"] = 0 if share_repost_type else 1  # 是否远程
        wb_item["weibo_from"] = wb_info["source"]  # 微博来源

        mid = wb_info["mid"]  # 微博的数字编号，拿图片/评论会用到

        img_list = []
        pic_ids = wb_info["pic_ids"]
        wimg_url_base = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}"

        for pid in pic_ids:
            wimg_url = wimg_url_base.format(user_id, mid, pid)
            img_list.append(wimg_url)
        wb_item["img_list"] = img_list  # 图片

        # 评论详情
        if wb_info["comments_count"]:
            comm_url_base = "https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&" \
                            "id={}&is_show_bulletin=2&is_mix=0&count=10&uid={}"
            comm_url = comm_url_base.format(mid, user_id)
            yield Request(comm_url, callback=self.get_comm,
                          meta={"superior_id": bid, "user_id": user_id, "comm_type": "root",
                                "comm_count": 0, "my_count": 0},
                          cookies=self.cookies, headers=self.comm_headers, dont_filter=True)
        links = []
        if wb_info.get("url_struct", []):
            for url_info in wb_info["url_struct"]:
                links.append(url_info["ori_url"])
        wb_item["links"] = links

        retweeted_status = wb_info.get("retweeted_status", 0)
        # 是否是转发微博，转发的记录r_href，源微博送去单条解析
        # 要处理这种能看见转发但原博不可阅读的：https://weibo.com/6591638928/IpXyxmLuO
        if retweeted_status:
            r_bid = wb_info["retweeted_status"]["mblogid"]
            try:
                r_user = wb_info["retweeted_status"]["user"]["idstr"]
                r_wb_url = "https://weibo.com/{}/{}".format(r_user, r_bid)
                r_href = "/{}/{}".format(r_user, r_bid)
                r_info_url = "https://weibo.com/ajax/statuses/show?id=" + r_bid
                print("{}的源微博为 {}".format(wb_item["wb_url"], r_wb_url))
                yield Request(r_info_url, callback=self.get_single_wb, cookies=self.cookies, headers=self.blog_headers,
                              meta={"count": 0}, dont_filter=True)
            except:
                remark += "无法获取源微博"
                r_href = ""

        else:
            r_href = ""

        # 暂且不写
        wb_item["t_bid"] = ""
        wb_item["r_href"] = r_href
        wb_item["r_weibo"] = {}
        wb_item["remark"] = remark
        wb_item["video_url"] = ""
        wb_item["article_url"] = ""
        wb_item["article_content"] = ""

        if retweeted_status:
            # 转发的直接送去入库
            print("{} 解析完毕:{}".format(wb_item["wb_url"], content[:10]))
            logging.debug("{} 解析完毕:{}".format(wb_item["wb_url"], content[:10]))
            yield wb_item
        else:
            # 原创的要做字数判断，过长的要单独一个请求获取完整内容
            text_len = wb_info.get("textLength")
            # 字数超过的送到获取长文的地方去，原content会被覆盖
            if text_len >= 240:
                longtext_url = "https://weibo.com/ajax/statuses/longtext?id={}".format(bid)
                yield Request(longtext_url, callback=self.get_long_text,
                              cookies=self.cookies, headers=self.blog_headers,
                              meta={"wb_item": wb_item, "count": 0}, dont_filter=True)
            else:
                print("{} 解析完毕:{}".format(wb_item["wb_url"], content[:10]))
                logging.debug("{} 解析完毕:{}".format(wb_item["wb_url"], content[:10]))
                yield wb_item

    def parse_comm(self, comm_info: dict, superior_id, user_id, comm_type):
        """
        解析评论，把需要的字段做成item，以及构建子评论请求
        :param comm_info: 薅来的评论信息
        :param comm_type: 评论类型，root或child
        :param superior_id: 上级的id
        :return: comm_item 和 该评论下子评论的请求
        """
        comm_item = commentItem()
        this_comm_num = 0
        comm_item["comment_type"] = comm_type
        # comm_item["superior_id"] = "//"+superior_id
        if comm_type == "root":
            comm_item["superior_id"] = "/{}/{}".format(self.user_id, superior_id)
        else:
            comm_item["superior_id"] = superior_id
        comment_id = comm_info["idstr"]
        comm_item["comment_id"] = comment_id
        content_parse = etree.HTML(comm_info["text"])
        content = " ".join(content_parse.xpath("//text()"))
        comm_item["content"] = content
        comm_item["user_name"] = comm_info["user"]["screen_name"]
        comm_item["user_url"] = "https://weibo.com" + comm_info["user"]["profile_url"]
        created_at = comm_info["created_at"]
        create_datetime = datetime.strptime(created_at, '%a %b %d %X %z %Y')
        create_time = datetime.strftime(create_datetime, "%Y-%m-%d %H:%M")
        comm_item["date"] = create_time
        comm_item["like_num"] = comm_info["like_counts"]
        comm_item["img_url"] = ""

        links = []
        if comm_info.get("url_struct", []):
            links_info = comm_info["url_struct"]
            for link_info in links_info:
                links.append(link_info["ori_url"])
        comm_item["link"] = links
        result_list = []  # 返回值
        result_list.append(comm_item)
        this_comm_num += 1
        # 是否有子评论，有的话送去请求
        if comm_info.get("comments", []):
            ccomm_url = "https://weibo.com/ajax/statuses/buildComments?is_reload=1&" \
                        "id={}&is_show_bulletin=2&is_mix=1&fetch_level=1&count=20&" \
                        "uid={}&max_id=0".format(comment_id, self.user_id)
            result_list.append(
                Request(ccomm_url, callback=self.get_comm,
                        meta={"superior_id": comment_id, "user_id": user_id, "comm_type": "child",
                              "comm_count": 0, "my_count": 0},
                        headers=self.comm_headers, cookies=self.cookies, dont_filter=True))
        return result_list

    def get_long_text(self, response):
        content = response.text
        j_data = json.loads(content)
        meta = response.meta
        meta["count"] += 1
        wb_item = meta["wb_item"]

        if j_data["ok"] and j_data["data"]:
            # 确实是长微博
            if j_data["data"]:
                content = j_data["data"]["longTextContent"]
                wb_item["content"] = content
            yield wb_item
            print("{} 解析完毕:{}".format(wb_item["wb_url"], content[:10]))
            logging.debug("{} 解析完毕:{}".format(wb_item["wb_url"], content[:10]))

        elif j_data["ok"]:
            # 判断是否长微博是用长度判断的，可能出现误判，获取长文本未返回数据
            # 这种情况直接用之前的短文本就行
            yield wb_item
        elif meta["count"] < 10:
            # 获取失败，再试试
            yield Request(response.request.url, callback=self.get_long_text,
                          cookies=self.cookies, headers=self.blog_headers,
                          meta=meta, dont_filter=True)
        else:
            logging.warning("{} 长文获取失败")
