# -*- coding: utf-8 -*-
import scrapy
import os
from datetime import datetime
import json
from scrapy import Request
import logging
from scrapy_weiboSpider import verify_info
from scrapy_weiboSpider.utils import time_utils, config_utils, file_utils, init_utils
from scrapy_weiboSpider.utils.log_print_utils import log_and_print
from scrapy_weiboSpider import skip_rules, parsers, fetcher


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
        config = config_utils.load_config(config_path)

        # 如果完全不获取评论，对主页的请求会过快导致被限制，间隔要加到 1.5
        comm_config = config["get_comm_num"]
        if not any(comm_config.values()) and config["get_rwb_detail"] == 0:
            print("本次运行不获取源微博和任何评论，请求间隔增加到 1.5s")
            crawler.settings.update({"DOWNLOAD_DELAY": 1.5})

        # 用配置文件弄出本次的redis_key更新到setting里
        keyword = config_utils.get_key_word(config)
        crawler.settings.update({
            "SCHEDULER_QUEUE_KEY": f"{keyword}:requests"}
        )
        logging.info(f"本次运行的配置文件为\n{json.dumps(config, indent=4)}")
        spider = cls(setting)
        spider._set_crawler(crawler)
        return spider

    def __init__(self, settings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config_utils.load_config(settings["CONFIG_PATH"])
        self.user_id = self.config["user_id"]
        # 目标和非目标评论数配置
        self.target_comm_config = {"wb_rcomm": self.config["get_comm_num"]["wb_rcomm"],
                                   "wb_ccomm": self.config["get_comm_num"]["wb_ccomm"]}

        self.no_target_comm_config = {"target_user_id": self.config["user_id"],
                                      "wb_rcomm": self.config["get_comm_num"]["rwb_rcomm"],
                                      "wb_ccomm": self.config["get_comm_num"]["rwb_ccomm"]}

        self.wb_time_start_limit = 0
        self.saved_all_bid = set()
        self.extra_log_path = f"log{os.path.sep}extra"
        if not os.path.exists(self.extra_log_path):
            os.makedirs(self.extra_log_path)

        self.continue_previous_run = init_utils.has_pending_requests_in_redis(settings)
        if self.continue_previous_run:
            log_and_print("检测到redis中有上次运行未完成的请求，将继续上次的爬取\n本次运行不会重新开始请求主页")

        # 登录信息
        self.cookies = config_utils.cookiestoDic(self.config["cookies_str"])
        self.blog_headers = verify_info.blog_headers_base
        self.blog_headers['x-xsrf-token'] = self.cookies["XSRF-TOKEN"]
        self.comm_headers = verify_info.comm_headers

    def start(self):
        # 录入之前的下载记录
        # saved_main_bid是打印用，只计算要爬的用户有多少微博
        # saved_all_bid是auto2模式去重用的
        result_filepath = config_utils.get_result_filepath(self.config)
        saved_main_bid, self.saved_all_bid = file_utils.load_save_bid(result_filepath)

        # 时间限制设定
        time_limit_config = self.config.get("time_limit", 0)
        self.wb_time_start_limit = init_utils.get_wb_time_start_limit(time_limit_config, result_filepath)

        # 提示信息
        init_utils.init_print(self.config, saved_main_bid, result_filepath, self.wb_time_start_limit)

        # 启动前按一下确认
        init_utils.confirm_start(self.config.get("ensure_ask", 1))

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
        debug_page_limit_reached = skip_rules.mainpage_debug_page_limit(self.config.get("debug", {}), page)
        if debug_page_limit_reached:
            log_and_print(f"【debug项】 页数限制{debug_page_limit_reached}，结束获取")
            return

        # 时间限制功能，本页及后面的页数都不需要获取
        stop_pagination, message = skip_rules.mainpage_stop_by_timelimit(
            wb_list, self.wb_time_start_limit)
        if stop_pagination:
            log_and_print(message)
            return

        # 本页面的解析
        # 有 no_sinceId_retry 说明这个请求是没获取到下一页的翻页参数后重试的，本页已经解析过了
        if meta.get("no_sinceId_retry", 0):
            message = "page {} 翻页重试次数 {}".format(page, meta.get("json_field_retry_count", -1))
            log_and_print(message, "debug")
        else:
            print("本页共微博微博{}条，开始解析".format(len(wb_list)))
            # 循环，塞方法里解析
            exist_null_wb = 0
            for wb_info in wb_list:
                # 一些过滤条件
                filter_status, filter_message = skip_rules.mainpage_wb_filter(
                    wb_info, self.user_id, self.config["time_limit"], self.wb_time_start_limit, self.saved_all_bid)
                if filter_status:
                    if "time limit" in filter_message:
                        create_timestamp = filter_message.split(":")[-1]
                        message = f"当前微博 {wb_info['mblogid']} ，发布时间 {time_utils.to_datetime(create_timestamp)}，时间限制 {time_utils.to_datetime(self.wb_time_start_limit)}，跳过本条微博解析"
                        log_and_print(message, "info")
                    elif "auto2 limit" in filter_message:
                        bid = filter_message.split(":")[-1]
                        message = f"auto2：当前微博 {bid} 已在文件中，跳过本条微博解析"
                        log_and_print(message, "info")
                    elif filter_message == "filter like":  # 过滤点赞
                        pass
                    else:
                        log_and_print(f"微博过滤:过滤状态信息{filter_message}")
                    continue

                # 送去解析

                ele_generator = parsers.parse_wb(
                    wb_info, self.config["get_rwb_detail"], self.target_comm_config, self.no_target_comm_config,
                    self.cookies, self.blog_headers, self.comm_headers,
                    self.get_long_text, self.get_single_wb, self.parse_comms)
                status = next(ele_generator)  # 第一个返回是状态码
                if status == "ok":  # 正常解析，后续会传item和request回来
                    for ele in ele_generator:
                        yield ele
                elif status is None:
                    # 啥都没有说明这条解析大失败，打个标，出循环把整页信息留个档
                    exist_null_wb = 1
                    message = f"page {page} 出现完全无法获取的微博，本页请求链接{response.request.url}，本页响应链接{response.url}"
                    log_and_print(message, "error")
                else:
                    message = f"微博解析出现未知状态码 {status}"
                    log_and_print(message)

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
        turning_request = fetcher.build_mainpage_turning_request(
            response, self.user_id, callback=self.get_mymblog_page,
            cookies=self.cookies, headers=self.blog_headers)
        yield turning_request

    def parse_comms(self, response):
        """
        root评论和child评论都走这个方法解析&翻页，用meta["comm_type"]区别
        meta中必须有以下值
        上级id superior_id、评论类型 comm_type 、用户id user_id、
        评论计数 comm_fetched、根评论目标数 rcomm_target，子评论目标数（这部分之后要改成可选项）
        """
        content = response.text
        j_data = json.loads(content)
        meta = response.meta

        superior_id = meta["superior_id"]  # 上级的id
        blog_user_id = meta["blog_user_id"]  # 用户id
        comm_type = meta["comm_type"]  # 评论类型
        ccomm_target = meta["ccomm_target"]
        rcomm_target = meta["rcomm_target"]

        comms = j_data["data"]  # 获取到的评论数据，是个list，一条一个评论
        # 评论一条一条塞到解析方法里
        for comm in comms:
            # 提取item
            comm_item = parsers.extract_comm_item(comm, superior_id, comm_type)
            yield comm_item
            meta["comm_fetched"] += 1  # 确认送去解析再 +1

            comment_id = comm_item["comment_id"]
            # 是否有子评论，有的且需要的话送去请求
            if comm.get("comments", []) and ccomm_target:
                yield fetcher.build_firse_ccomment_request(
                    comment_id, blog_user_id, rcomm_target, ccomm_target,
                    self.parse_comms, self.comm_headers, self.cookies)

        message = "获取到{} comm {} 条，上级为 {}，重试{}次". \
            format(comm_type, len(comms), superior_id, meta.get("failure_with_max_id", 0))
        log_and_print(message, "debug")

        # 下一页评论
        comment_turning_gen = fetcher.build_comment_turning_request(
            response, self.cookies, self.comm_headers, self.parse_comms)

        status, message = next(comment_turning_gen)

        if status == "ok":  # 有且要继续翻页，会再反一个request回来
            comment_turning_request = next(comment_turning_gen)
            yield comment_turning_request
        elif status == "wb limit":  # 微博限制评论显示
            message = f"{superior_id} 下 {comm_type} 状态： {message}，结束获取该条微博评论"
            log_and_print(message, "debug")
        elif status == "no max_id":  # 没有下一页
            message = f"{blog_user_id}/{superior_id} 无更多评论，获取结束"
            log_and_print(message, "debug")
        elif status == "comm_limit":  # 已获取设定的条数
            message = f"{comm_type} {blog_user_id}/{superior_id} 已经获取足够评论条数{message} "
            log_and_print(message, "debug")

    def get_long_text(self, response):
        """
        这里是只用来获取长微博文本的
        :param response: meta必须带一个已经提取出来的wb_item
        :return:
        """
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
        else:
            log_and_print("{} 长文获取失败", "warn")
            yield wb_item

    def get_single_wb(self, response):
        """
        获取单条微博
        :param response:
        :return:
        """
        content = response.text
        wb_info = json.loads(content)

        filter_status, filter_message = skip_rules.mainpage_wb_filter(
            wb_info, self.user_id, self.config["time_limit"], self.wb_time_start_limit, self.saved_all_bid)
        if filter_status:
            if "time limit" in filter_message:
                create_timestamp = filter_message.split(":")[-1]
                message = f"当前微博 {wb_info['mblogid']} ，发布时间 {time_utils.to_datetime(create_timestamp)}，时间限制 {time_utils.to_datetime(self.wb_time_start_limit)}，跳过本条微博解析"
                log_and_print(message, "info")
            elif "auto2 limit" in filter_message:
                bid = filter_message.split(":")[-1]
                message = f"auto2：当前微博 {bid} 已在文件中，跳过本条微博解析"
                log_and_print(message, "info")
            elif filter_message == "filter like":  # 过滤点赞
                pass
            else:
                log_and_print(f"微博过滤:过滤状态信息{filter_message}")
            return

        ele_generator = parsers.parse_wb(
            wb_info, self.config["get_rwb_detail"], self.target_comm_config, self.no_target_comm_config,
            self.cookies, self.blog_headers, self.comm_headers,
            self.get_long_text, self.get_single_wb, self.parse_comms)
        status = next(ele_generator)  # 第一个返回是状态码

        if status == "ok":  # ok的后续会传item和request回来
            for ele in ele_generator:
                yield ele
            # 该条跳过或者一些异常
        elif status is None:
            # 有一些微博直接看不了，但是在转发里能看到 例：OuOJfjgfu
            # 传到这里的有一些是从转发微博来的，meta里会带被转微博的信息
            # 带了的话就把带的部分解析出来
            meta = response.meta
            retweeted_status = meta.get("retweeted_status", {})
            if retweeted_status:
                log_and_print(f"微博 {response.request.url} 获取失败，将对携带的retweeted信息进行解析", "warn")
                retweeted_item = parsers.extract_wb_item(retweeted_status)
                yield retweeted_item
            else:
                log_and_print(f"微博 {response.request.url} 获取失败", "warn")
                return
        else:
            message = f"微博解析部分异常，状态码{status}"
            log_and_print(message, "error")
