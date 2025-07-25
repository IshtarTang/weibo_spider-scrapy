# -*- coding: utf-8 -*-
import scrapy
import os
from datetime import datetime
import json
import time
import sys
import re
from lxml.html import etree
from scrapy import Request
import msvcrt
import logging
from scrapy_weiboSpider.items import weiboItem, commentItem
from spider_tool import comm_tool
import redis


def write_json(obj1, filename="test.json"):
    json.dump(obj1, open(filename, "w", encoding="utf-8"), indent=4, ensure_ascii=False)


def timestamp_to_str(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S",
                         time.localtime(timestamp / 1000))


def log_and_print(message, log_level="info", print_end="\n"):
    if log_level == "info" or log_level == "INFO":
        logging.info(message)
        print(message, end=print_end)
    elif log_level == "warn" or log_level == "WARN":
        logging.warning(message)
        print(message, end=print_end)
    elif log_level == "debug" or log_level == "DEBUG":
        logging.debug(message)
        print(message, end=print_end)
    else:
        print(message, end=print_end)


class WeiboSpiderSpider(scrapy.Spider):
    # custom_settings = {
    #     "DOWNLOADER_MIDDLEWARES": {
    #         'scrapy_weiboSpider.middlewares.ScrapyWeibospiderDownloaderMiddleware': 543,
    #     }
    # }
    name = 'new_wb_spider'
    allowed_domains = ['weibo.com']

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # spider = super().from_crawler(crawler, *args, **kwargs)
        setting = crawler.settings
        config_path = setting["CONFIG_PATH"]
        with open(config_path, "r", encoding="utf-8") as op:
            config_str = op.read()
        config = json.loads(config_str)
        # 如果完全不获取评论，对主页的请求会很快，间隔要加到1
        comm_config = config["get_comm_num"]
        if not any(comm_config.values()) and config["get_rwb_detail"] == 0:
            print("本次运行不获取源微博和任何评论，请求间隔增加到 1.5s")
            crawler.settings.update({"DOWNLOAD_DELAY": 1.5})

        # 用配置文件弄出本次的redis_key更新到setting里
        keyword = comm_tool.get_key_word(config)
        crawler.settings.update({
            "SCHEDULER_QUEUE_KEY": f"{keyword}:requests"}
        )
        logging.info(f"本次运行的配置文件为\n{config_str}")
        spider = cls(setting)
        spider._set_crawler(crawler)
        return spider

    def __init__(self, settings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = json.load(open(settings["CONFIG_PATH"], "r", encoding="utf-8"))
        self.user_id = self.config["user_id"]
        self.key_word = comm_tool.get_key_word(self.config)
        self.wb_time_start_limit = 0
        self.saved_all_bid = set()
        self.extra_log_path = f"log{os.path.sep}extra"
        if not os.path.exists(self.extra_log_path):
            os.makedirs(self.extra_log_path)

        continue_previous_run = 0
        redis_host = settings.get("REDIS_HOST", '127.0.0.1')
        redis_port = settings.getint("REDIS_PORT", 6379)
        r = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        redis_requests_key = settings.get("SCHEDULER_QUEUE_KEY", "")
        if r.zcard(redis_requests_key) > 0:
            log_and_print("检测到redis中有上次运行未完成的请求，将继续上次的爬取\n本次运行不会重新开始请求主页")
            continue_previous_run = 1
        self.continue_previous_run = continue_previous_run

        self.cookies = comm_tool.cookiestoDic(self.config["cookies_str"])

        self.blog_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
            'cache-control': 'no-cache',
            'client-version': 'v2.44.79',
            'pragma': 'no-cache',
            'referer': 'https://weibo.com/',
            '^sec-ch-ua': '^\\^Google',
            'sec-ch-ua-mobile': '?0',
            '^sec-ch-ua-platform': '^\\^Windows^\\^^',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'server-version': 'v2024.04.01.2',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'x-xsrf-token': self.cookies["XSRF-TOKEN"],
        }

        self.comm_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
        }

    def start(self):
        """
        一些打印输出；读上次获取完成的微博，制成self.saved_all_bid
        """
        print("\n本次运行的文件key为 {}".format(self.key_word))
        comm_config_str = {"wb_rcomm": "微博根评论", "wb_ccomm": "微博子评论", "rwb_rcomm": "源微博根评论",
                           "rwb_ccomm": "源微博子评论"}
        print("评论获取设置：")
        for comm_config in self.config["get_comm_num"]:
            get_comm_num = self.config["get_comm_num"][comm_config]
            print("    {}:{}".format(comm_config_str[comm_config],
                                     get_comm_num if get_comm_num != -1 else "all"))
        #############
        # 录入之前的下载记录
        #############
        # saved_main_bid是打印用，只计算要爬的用户有多少微博，saved_all_bid是auto2模式去重用的
        save_main_bid = set()
        saved_path = comm_tool.get_result_filepath(self.config)
        saved_wb_filepath = os.path.join(saved_path, "wb_result.json")
        save_rwb_filepath = os.path.join(saved_path, "r_wb_result.json")
        if os.path.exists(saved_wb_filepath):
            saved_wb_data = json.load(open(saved_wb_filepath, "r", encoding="utf-8"))
            for wb_info in saved_wb_data:
                self.saved_all_bid.add(wb_info["bid"])
                save_main_bid.add(wb_info["bid"])
            if save_main_bid:
                log_and_print(
                    f"\n录入 {saved_wb_filepath} 的微博下载记录\n读取到上次运行保存的微博{len(self.saved_all_bid)}条")
            else:
                log_and_print(f"\n{saved_wb_filepath} 为空，无上次运行记录")

        if os.path.exists(save_rwb_filepath):
            saved_r_wb_data = json.load(open(save_rwb_filepath, "r", encoding="utf-8"))
            for r_wb_info in saved_r_wb_data:
                self.saved_all_bid.add(r_wb_info["bid"])

        ##############
        # 时间限制设定
        #############
        time_limit_config = self.config.get("time_limit", 0)
        print("时间限制设定为", time_limit_config)
        # 只获取 now - 设定时间的微博
        if time_limit_config == "auto":  # 自动模式，读取之前获取的最后一条微博时间，此前的微博不再次获取
            self.wb_time_start_limit = comm_tool.get_last_wb_public_time(saved_wb_filepath)
            if self.wb_time_start_limit == 0:  # 没有进度文件
                log_and_print("已启动自动时间限制，未检查到记录文件，将获取所有微博")
            else:  # 有进度文件
                wb_time_start_limit_str = time.strftime("%Y-%m-%d %H:%M:%S",
                                                        time.localtime(self.wb_time_start_limit / 1000))
                log_and_print(f"已启动自动时间限制，本次将获取 now - {wb_time_start_limit_str} 的微博到文件中")
        elif time_limit_config == "auto2":
            # auto2模式是按已保存过的bid判断的，不做时间限制
            self.wb_time_start_limit = 0
            log_and_print(f"已启用auto2模式，本次将获取所有 {saved_wb_filepath} 和 {save_rwb_filepath} 未保存的微博")


        elif (isinstance(time_limit_config, str)
              and re.search(r"[12]\d\d\d-[012]\d-[0123]\d [012]\d:[012345]\d",
                            str(time_limit_config))):  # 手动模式，yyyy-mm-dd hh:MM格式
            self.wb_time_start_limit = int(time.mktime(time.strptime(time_limit_config, "%Y-%m-%d %H:%M")) * 1000)
            print(f"已启动手动时间限制，配置类型str，本次将获取 now - {time_limit_config} 的微博到文件中")
        elif isinstance(time_limit_config, int):  # 手动模式，毫秒级时间戳
            self.wb_time_start_limit = time_limit_config
            wb_time_start_limit_str = \
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.wb_time_start_limit / 1000))
            print(f"已启动手动时间限制，配置类型毫秒时间戳，本次将获取 now - {wb_time_start_limit_str} 的微博到文件中")
        else:
            self.wb_time_start_limit = 0
            print(f"配置项 时间限制 {time_limit_config} 无效")
        print("请确认redis已启动，按任意键继续，或Esc以退出")
        if self.config.get("ensure_ask", 1):
            x = ord(msvcrt.getch())
            if x == 27:
                print("程序退出")
                logging.info("主动退出")
                import sys
                sys.exit(0)

    def start_requests(self):
        self.start()
        # redis里有上次没运行完的，这次不会再从主页翻
        if self.continue_previous_run:
            return
        start_page = 1
        # 调试项，设定起始页
        if self.config.get("debug", {}).get("on", {}):
            debug_start_page = self.config["debug"].get("page_start", -1)
            if debug_start_page != -1:
                start_page = debug_start_page
                log_and_print(f"【debug项】 起始页为 {debug_start_page}")

        start_url = "https://weibo.com/ajax/statuses/mymblog?" \
                    "uid={}&page={}&feature=0".format(self.user_id, start_page)
        yield Request(start_url, callback=self.get_mymblog_page,
                      cookies=self.cookies, headers=self.blog_headers,
                      meta={"ok1_retry": 0, "json_field_retry": [["data", "list"]],
                            "json_field_retry_allow_empty": True},
                      dont_filter=True)

    def get_mymblog_page(self, response):
        """
        处理用户主页的数据

        这里有一种情况，就是未成功获取到 微博list，但since_id有效且可以继续翻页的情况
        不过微博列表没获取到应该是整页都无效，如果出这个问题我再来处理
        """
        page = int(response.request.url.split("page=")[1].split("&")[0])
        log_and_print("已请求page {} 页面".format(page), print_end="\t")

        content = response.text
        j_data = json.loads(content)
        meta = response.meta
        wb_list = j_data["data"]["list"]

        # 调试项，页数限制
        if self.config.get("debug", {}).get("on", {}):
            page_limit = self.config["debug"].get("page_limit", -1)
            if page_limit != -1 and page >= page_limit:
                log_and_print(f"【debug项】 页数限制{page_limit}，结束获取")
                return

        # 时间限制功能
        if self.wb_time_start_limit != 0:
            # 找当前页最新一条微博
            weibos_create_at = [
                datetime.strptime(weibo_info.get("created_at", "Thu Jan 01 00:00:00 +0000 1970"),
                                  '%a %b %d %X %z %Y').timestamp() for weibo_info in wb_list
            ]
            current_page_latest_timestamp = max(weibos_create_at) * 1000  # 微博用的毫秒时间戳
            # 如果本页最新一条比限制时间早，直接截断
            if current_page_latest_timestamp <= self.wb_time_start_limit:
                log_and_print("时间限制{}，{}页最新微博时间 {}，主页获取结束".format(
                    timestamp_to_str(self.wb_time_start_limit), page, timestamp_to_str(current_page_latest_timestamp)))
                return

        # 本页面的解析
        # 有 no_sinceId_retry 说明这个请求是没获取到下一页的翻页参数后重试的，本页已经解析过了
        if meta.get("no_sinceId_retry", 0):
            message = "page {} 翻页重试次数 {}".format(page, meta.get("json_field_retry_count", -1))
            print(message)
            logging.debug(message)
        else:
            print("本页共微博微博{}条，开始解析".format(len(wb_list)))
            # 循环，塞方法里解析
            exist_null_wb = 0
            for wb_info in wb_list:
                if "赞过" in wb_info.get("title", {}).get("text", ""):
                    # 过滤掉主页的点赞
                    continue
                ele_generator = self.parse_wb(wb_info, self.config.get("get_rwb_detail", 1))
                tmp_ele = next(ele_generator)
                if tmp_ele is None:
                    # 啥都没有说明这条解析大失败，打个标，出循环把整页信息留个档
                    exist_null_wb = 1
                    del ele_generator
                elif isinstance(tmp_ele, str):
                    # str会描述为什么这条不解析
                    log_and_print(tmp_ele, "debug")
                    del ele_generator
                elif isinstance(tmp_ele, weiboItem) or isinstance(tmp_ele, Request):
                    # 正常解析出item和url，一条一条扔过去
                    yield tmp_ele
                    for ele in ele_generator:
                        yield ele
                else:
                    message = "微博解析部分出了问题，你返回了个啥赶紧查一下"
                    logging.error(message, tmp_ele)
                    print(message, tmp_ele)

            if exist_null_wb:
                info_filename = f"{self.config['user_id']}_{page}_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.json"
                info_path = os.path.join(self.extra_log_path, info_filename)
                with open(info_path, "w", encoding="utf-8") as op:
                    op.write(json.dumps(self.config))
                    op.write(f"page {page}")
                    op.write(content)
                logging.warning(
                    f"page {page} 出现完全无法获取的微博，本页请求链接{response.request.url}，本页响应链接{response.url}\n本页完整信息保存于{info_path}")

        # 翻页
        since_id = j_data["data"]["since_id"]
        if since_id:  # 有下一页
            # 把下一页的链接送进去
            next_url = "https://weibo.com/ajax/statuses/mymblog?" \
                       "uid={}&page={}&feature=0&since_id={}".format(self.user_id, page + 1, since_id)
            yield Request(next_url, callback=self.get_mymblog_page,
                          meta={"ok1_retry": 0,
                                "json_field_retry": [["data", "list"]],
                                "json_field_retry_allow_empty": True},
                          dont_filter=True, cookies=self.cookies, headers=self.blog_headers)
        else:  # 有时候会出现页面有内容但没有翻页id的情况 ，把翻页id作为必要响应内容扔回去重新请求
            new_request = response.request.copy()
            new_request.meta["json_field_retry"] = [["data", "since_id"]]
            new_request.meta["no_sinceId_retry"] = 1  # 设了这个之后就不会再解析一次该页的微博内容
            yield new_request

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
        # comm_count += len(comms)
        max_id = j_data["max_id"]  # max_id用于获取下一页评论
        # 评论一条一条塞到解析方法里
        for comm in comms:
            commItem_and_rcommReqs = self.parse_comm(comm, superior_id, user_id, comm_type)
            for c_or_i in commItem_and_rcommReqs:
                yield c_or_i
            comm_count += 1  # 确认送去解析再 +1
        message = "获取到{} comm {} 条，上级为 {}，重试{}次". \
            format(comm_type, len(comms), superior_id, meta.get("failure_with_max_id", 0))
        log_and_print(message, "debug")

        # #### 以下是翻页部分 ##########
        # 确定评论限制多少数量
        comm_limit = sys.maxsize
        comm_limit_config = self.config.get("get_comm_num", {})
        if comm_limit_config:
            # 是该用户的原创微博
            if str(self.config["user_id"]) == str(user_id):
                if comm_type == "root":  # 根评论
                    comm_limit = comm_limit_config["wb_rcomm"] if comm_limit_config["wb_rcomm"] != -1 else sys.maxsize
                else:  # 子评论
                    comm_limit = comm_limit_config["wb_ccomm"] if comm_limit_config["wb_ccomm"] != -1 else sys.maxsize
            # 被转发的微博
            else:
                if comm_type == "root":
                    comm_limit = comm_limit_config["rwb_rcomm"] if comm_limit_config["rwb_rcomm"] != -1 else sys.maxsize
                else:
                    comm_limit = comm_limit_config["rwb_ccomm"] if comm_limit_config["rwb_ccomm"] != -1 else sys.maxsize
        message = f"用户id {user_id}，类型 {comm_type}，评论限制{comm_limit}，当前数量{comm_count}，上级 {superior_id}"
        log_and_print(message, "debug")

        # 有max_id说明有下一页，如果没到限制的数量或者不限制（-1是不限制），把下一页的url弄出来
        if max_id and (comm_count < comm_limit or comm_limit == -1):
            o_url = response.request.url
            next_url = o_url.split("&max_id=")[0] + "&max_id=" + str(max_id)
            if "count=10" in next_url:  # 第一轮root评论的count是10，后面的和子评论的count都是20
                next_url = next_url.replace("count=10", "count=20")
            next_meta = {"superior_id": superior_id, "user_id": user_id, "comm_type": comm_type,
                         "comm_count": comm_count, "ok1_retry": 0}

            # 一些异常情况
            if len(comms) == 0:
                # 评论显示被限制的情况，能一直翻但实际上不会返回新评论，停止继续翻
                trends_text = j_data["trendsText"]
                if trends_text in ["博主已开启评论精选", "博主已开启防火墙，部分内容暂不展示", "已过滤部分评论",
                                   "由于博主设置，部分评论暂不展示"]:
                    message = f"{superior_id} 下 {comm_type} 状态： {trends_text}，结束获取该条微博评论"
                    logging.debug(message)
                    print(message)
                    return
                elif trends_text == "已加载全部评论":
                    # 另一种更迷惑的情况，需要点[加载更多]15次才能获取到下一页数据(一个例子 NFsyODei3)
                    # 出现这种情况就开始在meta计数，如果计到16还获取不到就放弃
                    # “已加载全部评论”是微博默认trends_text，就算后面还有评论也显示这个。这里其实是默认如果没有其他异常就翻15次
                    failure_with_max_id = meta.get("failure_with_max_id", 0)
                    next_meta["failure_with_max_id"] = failure_with_max_id + 1
                    if failure_with_max_id >= 16:
                        message = f"{superior_id} 下 {comm_type} 评论无法完整获取，评论链接{o_url}"
                        print(message)
                        logging.warning(message)
                        return

                else:
                    message = (f"评论 {response.url} 未获取到内容，上级链接{superior_id}，"
                               f"类型{comm_type}，下个链接{next_url}，当前内容 \n{content}")
                    logging.warning(message)
                    print(message)

            yield Request(next_url, callback=self.get_comm, priority=15,  # 这里用了高优先级
                          meta=next_meta, dont_filter=True, cookies=self.cookies, headers=self.comm_headers, )
        if comm_count >= comm_limit and comm_limit != -1:
            logging.debug(
                "{}/{} {}已经获取足够评论条数 get {} limit{}"
                .format(user_id, superior_id, response.url, comm_count, comm_limit))

    def get_single_wb(self, response):
        """
        获取单条微博
        :param response:
        :return:
        """
        content = response.text
        wb_info = json.loads(content)
        ele_generator = self.parse_wb(wb_info, self.config.get("get_rwb_detail", 1))
        tmp_ele = next(ele_generator)
        if tmp_ele is None:
            # 啥都没有说明这条解析大失败
            del ele_generator
            # 有一些微博直接看不了，但是在转发里能看到 例：OuOJfjgfu
            # 传到这里的有一些是从转发微博来的，meta里会带被转微博的信息
            # 带了的话就把带的部分解析出来
            meta = response.meta
            retweeted_status = meta.get("retweeted_status", {})
            if retweeted_status:
                log_and_print(f"微博 {response.request.url} 获取失败，将对携带的retweeted信息进行解析", "warn")
                retweeted_item = self.parse_wb_simple(retweeted_status, weiboItem())
                yield retweeted_item
            else:
                log_and_print(f"微博 {response.request.url} 获取失败", "warn")
                return
        elif isinstance(tmp_ele, str):
            # str会描述为什么这条不解析
            log_and_print(tmp_ele, "debug")
            del ele_generator
        elif isinstance(tmp_ele, weiboItem) or isinstance(tmp_ele, Request):
            # 正常解析出item和url，一条一条扔过去
            yield tmp_ele
            for ele in ele_generator:
                yield ele

    def parse_wb_simple(self, wb_info, wb_item, owb_url=""):
        """
        解析微博信息的一部分，可以是一条完整的也可以是转发页retweeted_status里的
        :param wb_info:从微博那扣来的，可以是完整信息也可以是retweeted_status
        :param wb_item:  可以是空的也可以是有一些数据的
        :param owb_url: 用来标识被转发微博是被哪条转发的，但是最后没加进去
        :return:加了解析出内容的wb_item
        """
        wb_item["remark"] = ""

        try:
            bid = wb_info["mblogid"]
            wb_item["bid"] = bid  # bid，微博的标识
            user_id = wb_info["user"]["idstr"]
            wb_item["user_id"] = user_id  # 用户id
        except:
            # bid和用户id获取不到说明这条微博完全无法看到
            logging.warning(f"{time.time()} 出现完全无法解析的微博，上阶段信息{wb_info}")
            return

        wb_item["wb_url"] = "https://weibo.com/{}/{}".format(wb_item["user_id"], wb_item["bid"])
        wb_item["user_name"] = wb_info["user"]["screen_name"]  # 用户名
        html_text = wb_info["text_raw"]  # 微博正文
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
        wb_item["weibo_from"] = wb_info["source"]  # 微博来源

        mid = wb_info["mid"]  # 微博的数字编号，拿图片/评论会用到
        # 获取图片
        img_list = []
        pic_ids = wb_info.get("pic_ids", [])
        wimg_url_base = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}"

        for pid in pic_ids:
            wimg_url = wimg_url_base.format(user_id, mid, pid)
            img_list.append(wimg_url)
        wb_item["img_list"] = img_list  # 图片

        # 链接
        links = []
        if wb_info.get("url_struct", []):
            for url_info in wb_info["url_struct"]:
                links.append(url_info["ori_url"])
        wb_item["links"] = links

        # 这些在完全解析里有，只走simple就需要补上这些
        wb_item["r_href"] = ""

        # 这些是
        wb_item["t_bid"] = ""
        wb_item["r_weibo"] = {}
        wb_item["video_url"] = ""
        wb_item["article_url"] = ""
        wb_item["article_content"] = ""

        retweeted_status = wb_info.get("retweeted_status", 0)
        wb_item["is_original"] = 0 if retweeted_status else 1  # 是否原创

        return wb_item

    def parse_wb(self, wb_info: dict, get_rwb_detail):
        """
        微博内容完全解析
        从响应的json里把需要的部分扣出来，做成item
        :param wb_info:
        :param get_rwb_detail: 要不要搞完整的源微博数据
        :return:三种情况，正常解析的反回含weibo_item和r_weibo&comm请求的迭代器，解析失败反回None，由于设置跳过当前微博的解析反回str
        """
        # 时间限制功能
        user_id = wb_info.get("user", {}).get("idstr", "")
        if self.wb_time_start_limit and user_id == self.config["user_id"]:
            created_at = wb_info.get("created_at", "Thu Jan 01 00:00:00 +0000 1970")
            create_timestamp = datetime.strptime(created_at, '%a %b %d %X %z %Y').timestamp() * 1000
            if create_timestamp < self.wb_time_start_limit:
                yield f"当前微博 {wb_info['mblogid']} ，发布时间 {timestamp_to_str(create_timestamp)}，时间限制 {timestamp_to_str(self.wb_time_start_limit)}，跳过本条微博解析"
        # auto2模式
        if self.config.get("time_limit", 0) == "auto2":
            bid = wb_info.get('mblogid', "")
            if bid in self.saved_all_bid:
                yield f"auto2：当前微博 {bid} 已在文件中，跳过本条微博解析"

        wb_item = weiboItem()
        wb_item = self.parse_wb_simple(wb_info, wb_item)
        if not wb_item:
            # 没获取到bid才会返回空，说明这条微博完全获取不到
            yield None
            return

        user_id = wb_item["user_id"]
        bid = wb_item["bid"]
        mid = wb_info["mid"]  # 微博的数字编号，拿图片/评论会用到

        # 是否获取评论
        is_get_comm = 0
        comm_configs = self.config["get_comm_num"]
        for comm_config_key in comm_configs:
            if comm_configs[comm_config_key] != 0:
                is_get_comm = 1
                break
        # 评论详情
        if is_get_comm and wb_info["comments_count"]:
            comm_url_base = "https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&" \
                            "id={}&is_show_bulletin=2&is_mix=0&count=10&uid={}"
            comm_url = comm_url_base.format(mid, user_id)
            yield Request(
                comm_url, callback=self.get_comm,
                meta={"superior_id": bid, "user_id": user_id, "comm_type": "root", "comm_count": 0, "ok1_retry": 0},
                cookies=self.cookies, headers=self.comm_headers,
                dont_filter=False)  # 这里是会去重的，单次运行时每条微博的评论只获取一次

        # 是否是转发微博，转发的记录r_href，源微博送去单条解析
        r_href = ""
        if not wb_item["is_original"]:  # 是一条转发微博
            r_bid = ""
            r_user = ""
            try:
                r_bid = wb_info["retweeted_status"].get("mblogid", "")  # 源微博bid
                r_user = wb_info["retweeted_status"].get("user", {}).get("idstr", "")  # 源微博用户id
            except:
                wb_item["remark"] += "无法获取源微博"

            if r_bid and r_user:  # 这两都有说明源微博可见
                r_wb_url = "https://weibo.com/{}/{}".format(r_user, r_bid)
                r_href = "/{}/{}".format(r_user, r_bid)
                r_info_url = "https://weibo.com/ajax/statuses/show?id=" + r_bid
                if get_rwb_detail:  # 是否获取源微博详情，默认获取，进行一次请求
                    print("{}的源微博为 {}，准备进行详细解析".format(wb_item["wb_url"], r_wb_url))
                    yield Request(r_info_url, callback=self.get_single_wb,
                                  cookies=self.cookies, headers=self.blog_headers,
                                  meta={"count": 0, "retweeted_status": wb_info["retweeted_status"]},
                                  dont_filter=False)
                else:  # 源微博走简单解析
                    print("{}的源微博为 {}，准备进行simple parse".format(wb_item["wb_url"], r_wb_url))
                    wb_item["remark"] += "设置为不获取详细源微博"
                    r_wb_item = self.parse_wb_simple(wb_info["retweeted_status"], weiboItem(), wb_item["wb_url"])
                    yield r_wb_item

        # 暂且不写
        wb_item["t_bid"] = ""
        wb_item["r_href"] = r_href
        wb_item["r_weibo"] = {}
        wb_item["video_url"] = ""
        wb_item["article_url"] = ""
        wb_item["article_content"] = ""

        if not wb_item["is_original"]:
            # 转发的不会超过字数，直接送去入库
            message = "{} r解析完毕:{}".format(wb_item["wb_url"], wb_item["content"][:10].replace("\n", "\t"))
            log_and_print(message, "DEBUG")
            yield wb_item
        else:
            # 原创的要做字数判断，过长的要单独一个请求获取完整内容
            text_len = wb_info.get("textLength", 240)
            # 字数超过的送到获取长文的地方去，原content会被覆盖
            if text_len >= 240:
                longtext_url = "https://weibo.com/ajax/statuses/longtext?id={}".format(bid)
                yield Request(longtext_url, callback=self.get_long_text,
                              cookies=self.cookies, headers=self.blog_headers,
                              meta={"wb_item": wb_item, "count": 0, "ok1_retry": 0}, dont_filter=True)
            else:
                message = "{} 解析完毕:{}".format(wb_item["wb_url"], wb_item["content"][:10].replace("\n", "\t"))
                log_and_print(message, "debug")
                yield wb_item

    def parse_comm(self, comm_info: dict, superior_id, user_id, comm_type):
        """
        解析评论，把需要的字段做成item，以及构建子评论请求
        :param comm_info: 薅来的评论信息
        :param superior_id: 上级的id
        :param user_id: 该微博的userid
        :param comm_type: 评论类型，root或child
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
        try:
            comm_item["like_num"] = comm_info["like_counts"]
        except KeyError:
            comm_item["like_num"] = -1
            logging.warning(f"点赞解析失败，设为-1，上级id {superior_id},类型 {comm_type}，当前comm {comm_info}")
        comm_item["img_url"] = ""

        links = []
        if comm_info.get("url_struct", []):
            links_info = comm_info["url_struct"]
            for link_info in links_info:
                link = link_info.get("ori_url", "")
                if not link:
                    link = link_info.get("long_url", "")
                links.append(link)
                if not link:
                    logging.warning(f"评论配图解析失败，上级id {superior_id},类型 {comm_type}，当前comm {comm_info}")

        comm_item["link"] = links
        result_list = [comm_item]  # 返回值
        this_comm_num += 1
        # 是否要获取子评论
        if comm_type == "root":
            if user_id == self.config["user_id"]:
                ccomm_limit = self.config["get_comm_num"]["wb_ccomm"]
            else:
                ccomm_limit = self.config["get_comm_num"]["rwb_ccomm"]
        elif comm_type == "child":
            ccomm_limit = 0
        else:
            ccomm_limit = 0
            logging.warning(f"parse_comm 评论类型异常 {comm_type} \n评论信息{comm_info}")

        # 是否有子评论，有的且需要的话送去请求
        if comm_info.get("comments", []) and ccomm_limit:
            ccomm_url = "https://weibo.com/ajax/statuses/buildComments?is_reload=1&" \
                        "id={}&is_show_bulletin=2&is_mix=1&fetch_level=1&count=20&" \
                        "uid={}&max_id=0".format(comment_id, self.user_id)
            result_list.append(
                Request(ccomm_url, callback=self.get_comm,
                        meta={"superior_id": comment_id, "user_id": user_id, "comm_type": "child",
                              "comm_count": 0, "ok1_retry": 0},
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
            message = "{} 解析完毕:{}".format(wb_item["wb_url"], content[:10].replace("\n", "\t"))
            log_and_print(message, "DEBUG")

        elif j_data["ok"]:
            # 判断是否长微博是用长度判断的，可能出现误判，获取长文本未返回数据
            # 这种情况直接用之前的短文本就行
            yield wb_item
        elif meta["count"] < 5:
            # 获取失败，再试试
            yield Request(response.request.url, callback=self.get_long_text,
                          cookies=self.cookies, headers=self.blog_headers,
                          meta=meta, dont_filter=True)
        else:
            logging.warning("{} 长文获取失败")
        return None
