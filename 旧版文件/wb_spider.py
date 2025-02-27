# -*- coding: utf-8 -*-


"""
这个是针对微博旧版UI的spider程序
由于旧版本UI的cookies已无法获取，且项目随新版spider做了很多修改，这一版已完全废弃
"""



import scrapy
import os
import json
import time
import sys
import math
from lxml.html import etree
import traceback
import re
from scrapy import Request
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
import requests
import msvcrt
import logging
from scrapy_weiboSpider.items import weiboItem, commentItem
from scrapy_weiboSpider.config_path_file import config_path
from spider_tool import comm_tool


class WeiboSpiderSpider(scrapy.Spider):
    custom_settings = {
        'LOG_FILE': comm_tool.get_log_path(),
    }
    name = 'wb_spider'
    allowed_domains = ['weibo.com']
    config = json.load(open(config_path, "r", encoding="utf-8"))
    key_word = comm_tool.get_key_word(config)
    saved_key = []
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"}
    cookies = comm_tool.cookiestoDic(config["cookies_str"])

    # 制造requests session
    session_start_time = time.time()
    session = requests.session()
    session.headers = headers
    session.cookies.update(cookies)

    def start(self):
        if not comm_tool.check_config(self.config):
            print("配置文件错误，按任意键退出")
            ord(msvcrt.getch())
            exit()
        else:
            print("检查完成")
        print("\n本次运行的文件key为 {}".format(self.key_word))
        comm_config_str = {"wb_rcomm": "微博根评论", "wb_ccomm": "微博子评论", "rwb_rcomm": "源微博根评论",
                           "rwb_ccomm": "源微博子评论"}
        print("评论获取设置：", end="\t")
        for comm_config in self.config["get_comm_num"]:
            if self.config["get_comm_num"][comm_config] == -1:
                self.config["get_comm_num"][comm_config] = sys.maxsize
            get_comm_num = self.config["get_comm_num"][comm_config]
            print(" {}:{}".format(comm_config_str[comm_config],
                                  get_comm_num if not get_comm_num == sys.maxsize else "all"), end="   ")
        print("\n")

        # 录入之前的下载记录，避免重复爬取
        # if os.path.exists("./file" + "/" + self.key_word + "/wb_result.json"):
        #     print("\n目标路径下已有上次运行产生的文件，本次运行爬取的微博会更新到文件中")
        per_wb_path = "./file" + "/" + self.key_word + "/prefile/weibo.txt"
        result_path = "./file" + "/" + self.key_word + "/wb_result.json"
        saved_key_config = self.config.get("deubg", {}).get("saved_key_file", "")

        if os.path.exists(result_path):
            if "wb" in saved_key_config or not saved_key_config:
                saved_wbs = json.load(open(result_path, "r", encoding="utf-8"))
                for wb in saved_wbs:
                    self.saved_key.append(wb["bid"])
                if saved_wbs:
                    print("录入 {} 的微博下载记录".format(result_path))
                else:
                    print("{} 无记录".format(result_path))
        if os.path.exists(per_wb_path):
            if "pwb" in saved_key_config or not saved_key_config:
                file1 = open(per_wb_path, "r", encoding="utf-8").read().strip()
                tmp_str = "[" + ",".join(file1.split("\n")) + "]"
                file = json.loads(tmp_str, encoding="utf-8")
                for x in file:
                    self.saved_key.append(x["bid"])
                if file:
                    print("录入 {} 的微博下载记录".format(per_wb_path))
                else:
                    print("{} 无记录".format(per_wb_path))

        self.saved_key = list(set(self.saved_key))
        if self.saved_key:
            print("读取到上次运行保存的微博{}条".format(len(self.saved_key)))
        else:
            print("未读取到上次的记录")

        print("请确认redis已启动，按任意键继续，或Esc以退出")
        x = ord(msvcrt.getch())
        if x == 27:
            print("程序退出")
            logging.info("主动退出")
            os._exit(0)

    def session_get(self, url):
        """
        使用requests 的 session去get
        在解析部分有需要立刻返回结果的请求
        session30分钟会过期，所有如果跟上次调用session的时间间隔超过10分钟就更新session
        :param url:
        :return:
        """

        # 如果session创建时间超过10分钟，重置session
        if time.time() - self.session_start_time > 600:
            session = requests.session()
            session.headers = self.headers
            session.cookies.update(self.cookies)
            self.session_start_time = time.time()
            logging.info("session更新，更新时间{}".format(time.time()))
        response = ""
        for i in range(0, 3):
            response = self.session.get(url, timeout=30)
            break
        logging.debug("requests url {} 成功".format(url))
        return response

    def start_requests(self):
        self.start()
        # 网络测试
        ident, page_num = self.get_ident_and_page_num()
        print("成功获取到iden {}".format(ident))
        # 获取页数
        # page_num = self.get_page_num()
        # 第一部分和后两部分的链接不同，分两个连接
        first_part_url_base = "https://weibo.com/u/{}?page={}&is_all=1"
        sub_part_url_base = "https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100505&visible=0&is_all=1" \
                            "&profile_ftype=1&page={}&pagebar={}&pl_name=Pl_Official_MyProfileFeed__20" \
                            "&id=100505{}&script_uri=/{}/profile&feed_type=0&pre_page={}&domain_op=100505&__rnd={} "
        user_id = self.config["user_id"]

        # 正常的页数循环
        page_range = range(1, page_num + 1)
        # 调试项，强行指定页数，key不会变
        if self.config.get("debug", {}).get("page_range", 0):
            tmp_str = self.config["debug"]["page_range"]
            page_range = range(int(tmp_str.split("-")[0]), int(tmp_str.split("-")[1]) + 1)
            print("调试项启动，页数范围 {}".format(tmp_str))
        print("按任意键继续，或Esc以退出")
        # if not self.saved_key:
        x = ord(msvcrt.getch())
        if x == 27:
            print("程序退出")
            logging.info("主动退出")
            os._exit(0)

        for page in page_range:
            url1 = first_part_url_base.format(user_id, page)
            url2 = sub_part_url_base.format(page, 0, user_id, user_id, page, int(time.time() * 1000))
            url3 = sub_part_url_base.format(page, 1, user_id, user_id, page, int(time.time() * 1000))
            print("page {} 时间检查".format(page))
            # 有进行时间限定
            if self.config["time_range"]["enable"]:
                # 检查这一页是否需要进行请求
                self.later_flag = 1
                page_in_timerange = self.t_is_page_in_timerange(user_id, page)
                # 晚了，跳过该页
                if page_in_timerange == "later":
                    print("page{}晚于目标时间，跳过".format(page))
                    continue
                # 早了，结束循环
                elif page_in_timerange == "early":
                    print("page{}早于目标时间，页数获取结束".format(page))
                    break
            print("page {} 时间检查通过".format(page))

            yield Request(url1, self.parse_home_page, cookies=self.cookies, meta={"count": 1, "part": 1, "max_div": 0},
                          errback=self.deal_err, dont_filter=True, priority=1)
            yield Request(url2, self.parse_home_page, cookies=self.cookies, meta={"count": 1, "part": 2, "max_div": 0},
                          errback=self.deal_err, dont_filter=True)
            yield Request(url3, self.parse_home_page, cookies=self.cookies, meta={"count": 1, "part": 3, "max_div": 0},
                          errback=self.deal_err, dont_filter=True)

    def parse_home_page(self, response):

        meta = response.meta
        # part1 的div需要从一大堆script里面找，有些长所以单独写了个方法， part2和part3可以直接parse
        if response.meta["part"] == 1:
            divs = self.parse_div_from_part1_response(response)
        else:
            html_text = json.loads(response.text)["data"]
            parse = etree.HTML(html_text)
            try:
                divs = parse.xpath("//div[@tbinfo]")
            except:
                divs = []

        # 没找到divs就重新请求
        if not divs:
            meta["count"] += 1
            if meta["count"] > 4:
                logging.warning("主页链接{}请求失败次数过多，请确认该页是否有效".format(response.url))
                print("主页链接{}请求失败次数过多，请确认该页是否有效".format(response.url))
                return
            yield Request(response.url, self.parse_home_page, cookies=self.cookies, meta=meta, dont_filter=True,
                          errback=self.deal_err)

            return

        # 每条微博是一个div
        # 过滤掉点赞
        real_div_list = []
        filter_num = 0
        for div in divs:
            share_scope_ele = div.xpath(".//div[contains(@class,'WB_cardtitle_b')]")
            if share_scope_ele:
                he_like = share_scope_ele[0].xpath(".//span[@class='subtitle']")
                if he_like:
                    filter_num += 1
                    continue
            real_div_list.append(div)

        #  没有15条说明没获取完，重新获取
        if len(real_div_list) < 15:
            # 循环次数大于4次,说明只有这么多条，不再重复获取，继续解析。max_div用于确认当前div数量是能获取到的最大div。
            if meta["count"] > 4 and len(real_div_list) == meta["max_div"]:
                pass
            else:
                meta["max_div"] = len(real_div_list) if len(real_div_list) > meta["max_div"] else meta["max_div"]
                meta["count"] += 1
                yield Request(response.url, self.parse_home_page, cookies=self.cookies, meta=meta, dont_filter=True,
                              errback=self.deal_err)
                return
        # 开启了时间范围判定且该divs不在时间范围内，不做保存
        if self.config["time_range"]["enable"] \
                and not self.t_is_divs_in_time_range(real_div_list, True, True):
            return

        for div in real_div_list:
            comm_config = self.config["get_comm_num"]
            r_weibo_and_requests = self.parse_weibo_from_div(div, comm_config, "", True)
            for r_and_i in r_weibo_and_requests:
                yield r_and_i

    def get_root_comment(self, response):
        """
        :param response:
        :return:
        """
        response_html = json.loads(response.text, encoding="utf-8")["data"]["html"]
        comment_parse = etree.HTML(response_html)
        meta = response.meta

        root_comm_divs = comment_parse.xpath("//div[contains(@node-type,'comment_list')]/div[@comment_id]")

        # 没获取到根评论，重新获取，超过五次认定为失败
        if not root_comm_divs:
            if meta["count"] > 5:
                logging.warning("rcomm {} {} {}获取失败".format(meta["superior_id"], meta["rcomm_count"], response.url))
                return
            meta["count"] += 1
            yield Request(response.url, callback=self.get_root_comment, cookies=self.cookies, meta=meta,
                          dont_filter=True, errback=self.deal_err)
            return

        # 获取成功
        meta["rcomm_count"] += len(root_comm_divs)
        logging.info("{} 获取到rcomm {}，总记 {}".format(meta["superior_id"], len(root_comm_divs), meta["rcomm_count"]))
        print("{} 获取到rcomm {}，总记 {}".format(meta["superior_id"], len(root_comm_divs), meta["rcomm_count"]))

        # 循环每个comm div
        for root_comm_div in root_comm_divs:
            # 解析root评论，塞进pipeline
            comm_item = self.parse_comment_from_div(root_comm_div, "root", meta["superior_id"])
            yield comm_item

            # 子评论，这里解析出的部分只是out部分
            child_comment_divs = root_comm_div.xpath(".//div[@node-type='child_comment']/div[@comment_id]")
            root_comm_id = root_comm_div.xpath("./@comment_id")[0]
            # 解析出来塞进pipeline
            for child_comment_div in child_comment_divs:
                comm_item = self.parse_comment_from_div(child_comment_div, "child", root_comm_id)
                yield comm_item

            # 如果设定获取更多子评论
            if meta["comm_config"]["wb_ccomm"]:
                # 是否有折叠子评论
                sub_child_comment_url_part = root_comm_div.xpath(
                    ".//a[@action-type='click_more_child_comment_big']/@action-data")
                if sub_child_comment_url_part:
                    sub_child_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo&__rnd={}".format(
                        sub_child_comment_url_part[0], int(time.time() * 1000))
                    yield Request(sub_child_comment_url, self.get_child_comment, cookies=self.cookies,
                                  meta={"superior_id": root_comm_id, "count": 1, "comm_config": meta["comm_config"],
                                        "ccomm_count": len(child_comment_divs)}, errback=self.deal_err)

        # 如果未满足要求的评论数，尝试翻页
        if meta["rcomm_count"] < meta["comm_config"]["wb_rcomm"]:
            # 默认翻页
            next_url_part = comment_parse.xpath("//div[@node-type='comment_loading']/@action-data")
            # 点击加载更多的翻页
            if not next_url_part:
                next_url_part = comment_parse.xpath("//a[@action-type='click_more_comment']/@action-data")
            # 旧的翻页url，2016之前都是这种
            if not next_url_part:
                next_url_part = comment_parse.xpath("//a[contains(@class,'page next')]/span/@action-data")
            # 如果有翻页url，翻页
            if next_url_part:
                next_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo&__rnd={}". \
                    format(next_url_part[0], int(time.time() * 1000))
                # rcomm_count在前面加过，count重置为1，其他内容相同
                meta["count"] = 1

                yield Request(next_url, self.get_root_comment, meta=meta, errback=self.deal_err)

    def get_child_comment(self, response):
        """
        :param response:
        :return:
        """
        meta = response.meta
        root_comm_id = meta["superior_id"]
        response_html = json.loads(response.text, encoding="utf-8")["data"]["html"]
        comment_parse = etree.HTML(response_html)

        child_comment_divs = comment_parse.xpath("//div[@comment_id]")

        # 没找着
        if not child_comment_divs:
            meta = response.meta
            if meta["count"] > 5:
                logging.warning("{} 下子评论 {}+ 获取失败".format(root_comm_id, meta["ccomm_count"]))
                return
            meta["count"] += 1
            yield Request(response.url, self.get_child_comment, cookies=self.cookies, meta=meta, errback=self.deal_err)
            return

        # 这子评论解析代码跟 get_root_comment() 解析子评论部分的代码是重合的，但拆开思路清晰些，当然也有可能是我现在脑子有点转不动了
        # 解析，塞进pipeline
        for child_comment_div in child_comment_divs:
            comm_item = self.parse_comment_from_div(child_comment_div, "child", root_comm_id)
            yield comm_item

        try:
            meta["ccomm_count"] += len(child_comment_divs)
        except:
            logging.warning("meta_count无 {} ".format(meta))
        logging.info(
            "{} 获取到 rcomm {} 条，总计 {} 条".format(root_comm_id, len(child_comment_divs), meta["ccomm_count"]))
        print("{} 获取到 rcomm {} 条，总计 {} 条".format(root_comm_id, len(child_comment_divs), meta["ccomm_count"]))

        # 如果未到达要求的子评论数量
        if meta["ccomm_count"] < meta["comm_config"]["wb_ccomm"]:
            sub_child_comment_url_part = comment_parse.xpath(
                "//a[@action-type='click_more_child_comment_big']/@action-data")
            if sub_child_comment_url_part:
                sub_child_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo&__rnd={}".format(
                    sub_child_comment_url_part[0], int(time.time() * 1000))
                meta["count"] = 1
                yield Request(sub_child_comment_url, self.get_child_comment, cookies=self.cookies,
                              meta=meta, errback=self.deal_err)

    def get_single_wb(self, response):
        """
        这是个单条微博解析，链接为微博链接 如：https://weibo.com/5648729445/Kpu9wyarC
        要求meta中必须有 count，comm_config,wb_type。
        count为这条链接第几次请求，int；
        comm_config 要获取的评论数量 {"wb_rcomm": int,"wb_ccomm": int,"rwb_rcomm": int,"rwb_ccomm": int}
        wb_type:微博类型，o_wb 为原创微博，t_wb 为一条转发微博，r_wb 为一条转发微博的源微博
        wb_type 为 r_wb时，meta还需要有t_bid 和 t_div,t_bid为转发微博的bid，t_div为转发页的该条微博div
        :param response:
        :return:
        """
        url = response.url
        id_search = re.search(r"weibo.com/(\d+)/.*", url)
        user_id = id_search.group(1)
        scripts = response.xpath("/html/script").extract()
        weibo_parse = None
        for script in scripts:
            try:

                if "feed_list_content" in script and "ouid={}".format(user_id) in script:
                    # 提取出值中的json
                    tmp_str = re.search(r"\(({.*?feed_list_content.*?ouid=" + str(user_id) + ".*?})\)",
                                        script).group(1)
                    tmp_json = json.loads(tmp_str, encoding="utf-8")
                    # 获取html。符号编码不知道哪出问题了，手动替换
                    weibo_html = tmp_json["html"].replace("&lt;", "<").replace("&gt;", ">")
                    weibo_parse = etree.HTML(weibo_html)
                    break
            except:
                logging.warning(traceback.format_exc())
        meta = response.meta
        # 没获取到
        if not weibo_parse:
            # 获取次数小于6次，重新获取
            if meta["count"] < 6:
                meta["count"] += 1
                yield Request(response.url, self.get_single_wb, meta=meta, cookies=self.cookies,
                              errback=self.deal_err)
                return
            else:
                # 返回一个空
                # yield weiboItem()
                logging.warning("源微博 {} 获取失败".format(response.url))
                print("源微博 {} 获取失败".format(response.url))
                return
        # 获取到div，调用解析方法
        weibo_div = weibo_parse.xpath("//div[@tbinfo]")[0]
        request_and_item = self.parse_weibo_from_div(weibo_div, meta["comm_config"], meta["t_bid"], False)
        for r_or_i in request_and_item:
            yield r_or_i

    def parse_weibo_from_div(self, div, comm_config, t_bid, check_time):
        """
        解析微博div，yield评论url的Request、源微博url的Request（如果有的话）、解析出的wbItem
        这个方法不负责检查div是否是一个正常的有内容的div，如果解析不出内容会返回None，请在调用它的地方处理
        :param comm_config: {"wb_rcomm": int,"wb_ccomm": int,"rwb_rcomm": int,"rwb_ccomm": int}
        :param div: //div[@tbinfo] 是etree.HTML().xpath()
        :param t_bid: 如果这是条转发微博的源微博，t_bid是转发微博的bid，否则空
        :return:
        """
        remark = ""
        parse = div
        # 微博链接
        try:
            part_url = parse.xpath(".//div[contains(@class,'WB_from')]/a/@href")[0]
            weibo_url = "https://weibo.com" + part_url.split("?from")[0]
        except:
            print("调用parse_weibo_from_div的参数有误，返回空weibo对象")
            logging.warning("r wb解析失败 t_bid{}".format(t_bid))
            time.sleep(3)
            return
        logging.info("开始解析 {}  {}".format(weibo_url, t_bid))
        print("开始解析微博 {}".format(weibo_url))

        # bid
        bid_ele = parse.xpath(".//a[@node-type='feed_list_item_date']/@href")
        bid = re.search("/\d+/(\w+)\?", bid_ele[0]).group(1)
        logging.info("bid - {}".format(bid))

        ident = bid.split("/")[0]

        # 发表时间戳
        public_timestamp = int(parse.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])
        if check_time:
            if not self.t_is_time_in_range(public_timestamp):
                time_range_config = self.config["time_range"]
                tmp_content = parse.xpath(".//div[@node-type='feed_list_content']//text()")
                content = "\n".join(tmp_content).replace("\u200b", ""). \
                    replace("//\n@", "//@").replace("\n:", ":").replace("\xa0", "").replace("\xa1", "").strip()
                logging.info(
                    "当前微博[{}]{} 时间({})不在要求范围内[{}-{}]，被过滤掉"
                    .format(public_timestamp, content[:10], public_timestamp,
                            time_range_config["start_time"], time_range_config["stop_time"])
                )

                return

        # 用户名，同时判断是否为快转
        quick_transmit = 0
        user_name = parse.xpath(".//a[@class='W_f14 W_fb S_txt1']/text()")

        if not user_name:
            user_name = parse.xpath(".//a[contains(@class,'W_f14 W_fb S_txt1')]/text()")
            quick_transmit = 1
        user_name = user_name[0]

        # 是否为原创微博，转发微博源微博的相对地址
        trainsmig_ele = parse.xpath(".//div[contains(@class,'WB_feed_expand')]")
        if trainsmig_ele:
            # 是转发微博
            is_original = 0
            if len(bid_ele) > 1:
                r_href = bid_ele[1]
            else:
                r_href = ""

                remark += "源微博已不可见\t"
        else:
            if quick_transmit:
                # 是快转微博
                is_original = -1
            else:
                # 是原创微博
                is_original = 1
            r_href = ""

        # 正文
        # 文章长时会有收起的部分，需要另外发送请求
        is_content_long = parse.xpath(
            ".//div[contains(@class,'WB_feed_detail')]/div/div[contains(@class,'WB_text')]/a[contains(@class,'WB_text_opt')]")
        # 如果有折叠的部分，把url塞到解析单条微博的方法去解析微博正文页，这里不继续解析
        if is_content_long:
            meta = {"t_weibo_div": None, "t_bid": None, "wb_type": "o_wb", "count": 1,
                    "comm_config": comm_config, "handle_httpstatus_list": [302]}
            yield Request(weibo_url, callback=self.get_single_wb, cookies=self.cookies, meta=meta,
                          errback=self.deal_err, dont_filter=True)
            return
        else:
            content_ele = parse.xpath(".//div[@node-type='feed_list_content']//text()")
        # 取出0的首尾空格
        content_ele[0] = content_ele[0].strip()
        content = "\n".join(content_ele).replace("\u200b", "").replace("//\n@", "//@").replace("\n:", ":").replace(
            "\xa0", "").replace("\xa1", "")
        # 有链接时会多出换行，可以在xpath处理但是太麻烦，所以直接replace
        content = content.replace("\nO\n网页链接", " O 网页链接")

        # 源微博
        r_weibo = {}  # 先占个位，Pipeline里再写进去
        # 存在源微博，且源微博可见，
        if r_href and "源微博已不可见" not in remark:
            # 之前没有保存过源微博
            if r_href.split("/")[-1] not in self.saved_key:
                r_url = "https://weibo.com" + r_href
                if self.config["print_level"]:
                    print("微博为转发微博，源微博 {}".format(r_url))
                    logging.info("微博为转发微博，源微博 {}".format(r_url))
                meta = {}
                meta["t_weibo_div"] = etree.tostring(div).decode("utf-8")
                meta["t_bid"] = bid
                meta["wb_type"] = "r_wb"
                meta["count"] = 1
                # 源微博的 wb_rcomm 用的是当前的 rwb_rcomm。
                # 源微博的 rwb_rcomm 不会被用到（因为源微博不会有它的源微博），写啥都无所谓
                r_comm_config = {"wb_rcomm": comm_config["rwb_rcomm"],
                                 "wb_ccomm": comm_config["rwb_ccomm"],
                                 "rwb_rcomm": 0,
                                 "rwb_ccomm": 0}
                meta["comm_config"] = r_comm_config
                # 禁用重定向
                meta["dont_redirect"] = True
                meta["handle_httpstatus_list"] = [302]
                yield Request(r_url, callback=self.get_single_wb, cookies=self.cookies, meta=meta,
                              errback=self.deal_err, dont_filter=True)

            # 之前保存过
            else:
                print("微博为转发微博，源微博 {} 已保存过，跳过解析".format(r_href))
                logging.info("源微博 {} 已保存过，跳过解析".format("https://weibo.com" + r_href))

        if ident in self.saved_key:
            if self.config["print_level"]:
                logging.info("当前微博 {} 在之前已保存，跳过解析".format(bid))
                print("当前微博 {} 在之前已保存，跳过解析".format(bid))
            return

            # 用户id，微博为转发时格式为 ‘ouid=6123910030&rouid=5992829552’
        user_id_ele = parse.xpath(".//@tbinfo")[0].split("&")[0]
        user_id = re.search(r"ouid=(\d+)", user_id_ele).group(1)

        # 外链，微博有的链接进行一次请求才能获取到真正的链接，有的需要从确认界面中获取
        parse_links = parse.xpath(".//div[@node-type='feed_list_content']//a[@href and @rel]/@href")
        real_links = []
        for parse_link in parse_links:
            # try是有时候会有外网链接，请求失败
            try:
                link_response = self.session_get(parse_link)
                response_url = link_response.url

                if response_url != parse_link:
                    # 直接将请求到的url放入列表
                    real_links.append(response_url)
                else:
                    # 需要从页面中解析出真正的url
                    real_link = etree.HTML(link_response.text).xpath(".//div[contains(@class,'desc')]/text()")[
                        0].strip()
                    real_links.append(real_link)

            except:
                real_links.append(parse_link)

        # 可见范围
        share_scope_ele = parse.xpath(".//div[contains(@class,'WB_cardtitle_b')]")
        if share_scope_ele:
            share_scope = share_scope_ele[0].xpath(".//span[@class='WB_type']/text()")[0]
        else:
            share_scope = "公开"

        # 转发数
        forward_num_ele = parse.xpath(".//span[@node-type='forward_btn_text']//text()")
        forward_num = 0
        if forward_num_ele:
            forward_num_str = forward_num_ele[1]
            if forward_num_str != "转发":
                try:
                    forward_num = int(forward_num_str)
                except:
                    if "万" in forward_num_str:
                        forward_num = int(forward_num_str.split("万")[0]) * 10000
                        remark += "\t 转发数过大，获取到的字符串为：{}".format(forward_num_str)
                    else:
                        forward_num = -1
                        remark += "\t 转发数异常，获取到的字符串为：{}".format(forward_num_str)

        # 评论数
        comment_num_str = parse.xpath(".//span[@node-type='comment_btn_text']//text()")[1]
        if comment_num_str != "评论":
            try:
                comment_num = int(comment_num_str)
            except:
                if "万" in comment_num_str:
                    comment_num = int(comment_num_str.split("万")[0]) * 10000
                    remark += "\t 评论数过大，获取到的字符串为：{}".format(comment_num_str)
                else:
                    comment_num = -1
                    remark += "\t 评论数异常，获取到的字符串为：{}".format(comment_num_str)
        else:
            comment_num = 0
        # 点赞数
        # 是转发微博且原微博存在时 取下标1，否则0
        my_like_index = 1 if (not is_original and "源微博已不可见" not in remark) else 0
        # try:
        like_num_ele = parse.xpath(".//span[@node-type='like_status']")[my_like_index]

        like_num_str = like_num_ele.xpath(".//text()")[-1]
        if like_num_str != "赞":
            try:
                like_num = int(like_num_str)
            except:
                if "万" in like_num_str:
                    like_num = int(like_num_str.split("万")[0]) * 10000
                    remark += "\t 点赞数过大，获取到的字符串为：{}".format(like_num_str)
                else:
                    like_num = -1
                    remark += "\t 点赞数异常，获取到的字符串为：{}".format(like_num_str)
        else:
            like_num = 0

        # 发表时间
        public_time = str(parse.xpath(".//div[contains(@class,'WB_from')]/a/@title")[0])

        item_eles = parse.xpath(
            ".//div[contains(@class,'WB_media_wrap clearfix')]//div[contains(@class,'media_box')]")
        # 图片链接
        img_list = []

        # 存在item_ele
        if item_eles and is_original:

            item_ele = item_eles[0]
            imgs_src = item_ele.xpath(".//li[contains(@class,'WB_pic')]/img/@src")
            if imgs_src:
                mid = parse.xpath(".//div[contains(@class,'WB_from')]/a/@name")[0]
                for img_src in imgs_src:
                    img_id = img_src.split("/")[-1].split(".")[0]
                    wimg_url = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}".format(user_id, mid, img_id)
                    img_list.append(wimg_url)
        # 视频
        video_url = ""
        video_url_info = parse.xpath(".//li[contains(@class,'WB_video')]/@suda-uatrack")
        # 只保留原创视频链接
        if video_url_info and is_original:
            video_url_base = "https://weibo.com/tv/show/{}:{}"
            video_search = re.search(r":(\d+)%3A(\w+):", video_url_info[0])
            try:
                video_url = video_url_base.format(video_search.group(1), video_search.group(2))
            except AttributeError as e:
                remark += "\t 该条微博带有直播视频"

        # 微博来源
        weibo_from_ele = parse.xpath(".//div[contains(@class,'WB_from')]//a[@action-type]/text()")
        if weibo_from_ele:
            weibo_from = weibo_from_ele[0]
        else:
            weibo_from = "未显示来源"

        # 文章 链接和内容
        article_url = ""
        article_content = ""
        article_url_ele = parse.xpath(".//div[contains(@class,'WB_feed_spec')]/@suda-uatrack")

        # 存在外链div
        if article_url_ele:
            article_url_base = "https://weibo.com/ttarticle/p/show?id={}"
            article_id_search = re.search(r"article:（\d+）:", article_url_ele[0])
            # 外链div为文章
            if article_id_search:
                article_url = article_url_base.format(article_id_search.group(1))
                article_parse = etree.HTML(self.session_get(article_url).text)
                article_content = "\n".join(article_parse.xpath(".//div[@node-type='contentBody']/p/text()"))

        # 如果有评论，且设置要获取评论
        if comment_num and comm_config["wb_rcomm"]:
            id = parse.xpath(".//div[contains(@class,'WB_from')]/a/@name")[0]
            first_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&id={}&from=singleWeiBo&__rnd={}".format(
                id, int(time.time() * 1000))
            yield Request(first_comment_url, callback=self.get_root_comment, cookies=self.cookies,
                          meta={"comm_config": comm_config, "rcomm_count": 0, "superior_id": part_url.split("?")[0],
                                "count": 1, "wb_url": weibo_url}, dont_filter=True, errback=self.deal_err)

        # 话题，@的用户，地址    不想写，以后可能会补上
        topic_list = []
        call_users = []
        address = ""

        weiboItem1 = weiboItem()
        weiboItem1["bid"] = bid
        weiboItem1["t_bid"] = t_bid
        weiboItem1["wb_url"] = weibo_url
        weiboItem1["user_id"] = user_id
        weiboItem1["user_name"] = user_name
        weiboItem1["content"] = content
        weiboItem1["public_time"] = public_time
        weiboItem1["public_timestamp"] = public_timestamp
        weiboItem1["share_scope"] = share_scope
        weiboItem1["like_num"] = like_num
        weiboItem1["forward_num"] = forward_num
        weiboItem1["comment_num"] = comment_num
        weiboItem1["is_original"] = is_original
        weiboItem1["r_href"] = r_href
        weiboItem1["links"] = real_links
        weiboItem1["img_list"] = img_list
        weiboItem1["weibo_from"] = weibo_from
        weiboItem1["article_url"] = article_url
        weiboItem1["article_content"] = article_content
        weiboItem1["video_url"] = video_url
        weiboItem1["remark"] = remark
        weiboItem1["r_weibo"] = r_weibo

        yield weiboItem1

    def parse_comment_from_div(self, h_comment_div, comment_type, superior_id):
        """
        :param h_comment_div: //div[@comment_id]，我也不记得我为什么要加h_了。
        :param comment_type: root 或者 child
        :param superior_id: 上级id，root评论上级id为微博bid，child评论上级为root评论id
        :return: 一个评论item，返回后记得把返回值yield
        """
        comment_id = h_comment_div.xpath("./@comment_id")[0]
        logging.debug("开始解析 {} 评论 {} {}".format(comment_type, superior_id, comment_id))
        # 往下一层
        comment_div = h_comment_div.xpath("./div[contains(@class,'list_con')]")[0]
        # 一条root/child评论信息
        # 评论内容
        comment_content_and_user = "".join(comment_div.xpath("./div[contains(@class,'WB_text')]//text()")) \
            .encode("gbk", errors="replace").decode("gbk", errors="replace").strip()
        comment_content = comment_content_and_user.split("：", 1)[1].strip()
        # 评论人
        user_name = comment_div.xpath(".//div[contains(@class,'WB_text')]/a/text()")[0]
        # 评论人主页链接
        user_url = "https:" + comment_div.xpath(".//div[contains(@class,'WB_text')]/a/@href")[0]
        # 评论时间
        comment_date = comment_div.xpath(".//div[contains(@class,'WB_from')]/text()")[0]
        comment_date = self.n_deal_comment_date(comment_date)

        # 评论点赞数
        comment_like_eles = comment_div.xpath(".//span[@node-type='like_status']//text()")
        if comment_type == "root":
            comment_like_str = comment_like_eles[1]
        else:
            comment_like_str = comment_like_eles[-1]
        if comment_like_str != "赞":
            like_num = int(comment_like_str)
        else:
            like_num = 0
        # 评论带图
        comment_img_url = ""
        if comment_type == 'root':
            # root用跟child一样的方法也能获取到图片,但是写的这种获取的图片更高清
            img_ele = comment_div.xpath(".//li/img/@src")
            if img_ele:
                img_url = img_ele[0].replace("thumb180", "large")
                comment_img_url = img_url
        else:
            img_info = comment_div.xpath(".//a[@alt]/@action-data")
            if img_info:
                img_url_base = "https://wx3.sinaimg.cn/large/{}.jpg"
                img_pid = re.search("pid=(\w.*?)&", img_info[0])
                comment_img_url = img_url_base.format(img_pid.group(1))

        # 链接
        comment_link_ele = comment_div.xpath("./div[@class='WB_text']/a/@alt")
        real_comment_link = ""
        if comment_link_ele:
            comment_link = comment_link_ele[0]
            real_comment_link = comment_link
            try:
                real_comment_link = requests.get(comment_link, headers=self.headers, timeout=30).url
            except:
                pass
        commentItem1 = commentItem()

        commentItem1["comment_type"] = comment_type
        commentItem1["superior_id"] = superior_id
        commentItem1["comment_id"] = comment_id
        commentItem1["user_url"] = user_url
        commentItem1["content"] = comment_content
        commentItem1["user_name"] = user_name
        commentItem1["date"] = comment_date
        commentItem1["like_num"] = like_num
        commentItem1["img_url"] = comment_img_url
        commentItem1["link"] = real_comment_link

        return commentItem1

    def parse_div_from_part1_response(self, response):
        """
        用户主页第一页的div需要从一堆script里面找出来
        :param response: scrapy的response 或者requests的response
        :return:
        """
        # 先提出scripts 类型是str
        if isinstance(response, scrapy.http.HtmlResponse):
            scripts = response.xpath("//script").extract()
        elif isinstance(response, requests.models.Response):
            parse = etree.HTML(response.content.decode("utf-8"))
            script_eles = parse.xpath("//script")
            scripts = []
            for script_ele in script_eles:
                script = script_ele.text
                scripts.append(script)
        else:
            print("你传了个什么屌东西")
            print("位置 get_div_from_part1")
            return []
        # 提取正文的div
        divs = []
        for script in scripts[-1::-1]:
            """
            这里容易出问题，改过了不过说不定还是会出
            """
            if 'class=\\"WB_feed' in script:
                re_s = re.search(r"\(({.*?WB_feed.*?})\)", script.replace("\n", ""))
                try:
                    html_text = json.loads(re_s.group(1))["html"]
                    parse = etree.HTML(html_text)
                    divs = parse.xpath("//div[@tbinfo]")
                    break
                except:
                    continue

        return divs

    def n_deal_comment_date(self, comment_time: str):
        """
        评论时间太近会出现 "今天 20:20","10分钟前","10秒前"的格式，需要转为标准时间
        :param comment_time:
        :return:
        """
        comment_time = comment_time.split(" 来自")[0]
        if "今天" in comment_time:
            patten = "%Y-%m-%d"
            today_time = time.localtime(time.time())
            today_date_str = time.strftime(patten, today_time)
            comment_time_result = comment_time.replace("今天", today_date_str)
        elif "前" in comment_time:
            patten = "%Y-%m-%d %H:%M"
            if "秒" in comment_time:
                sec = int(comment_time.replace("秒前", ""))
                comment_timestamp = time.time() - sec
                comment_time_result = time.strftime(patten, time.localtime(comment_timestamp))
            elif "分钟" in comment_time:
                sec = int(comment_time.replace("分钟前", "")) * 60
                comment_timestamp = time.time() - sec
                comment_time_result = time.strftime(patten, time.localtime(comment_timestamp))

            else:
                comment_time_result = comment_time
                print("时间解析有误")
        else:
            comment_time_result = comment_time
        return comment_time_result

    def get_ident_and_page_num(self):
        """
        获取用户标识 用户名[用户id]，检测下网络
        :return:
        """
        user_id = self.config["user_id"]
        base_url = "https://weibo.com/u/{}?page=1&is_all=1".format(user_id)
        print("测试获取", base_url)
        count = 0
        flag = 0
        while True:
            count += 1
            first_part_response = self.session_get(base_url)
            parse = etree.HTML(first_part_response.text)
            scripts = parse.xpath("//script")
            user_ident = ""
            all_wb_num = 0
            page_num = 0
            for script in scripts[::-1]:
                # 从一堆script里提取html出来
                try:
                    re_s = re.search(r"\(({.*})\)", script.text.replace("\n", ""))
                    html_text = json.loads(re_s.group(1))["html"]
                    script_parse = etree.HTML(html_text)
                    open("./writeing.html", "w", encoding="utf-8").write(html_text)
                except (KeyError, AttributeError) as e:
                    continue
                if not user_ident:
                    try:
                        # 没搞到的话这里会直接抛报错
                        user_name = script_parse.xpath("//div[contains(@class,'WB_info')]/a/text()")[0]
                        user_ident = "{}[{}]".format(user_name, user_id)

                    except (IndexError, AttributeError) as e:
                        """这是正常流程"""
                        pass

                if not all_wb_num:
                    try:
                        all_wb_num = script_parse.xpath(
                            "//table[@class='tb_counter']//td[3]//a[@bpfilter='page_frame']/strong/text()")[0]
                        all_wb_num = int(all_wb_num)
                        print("总微博条数 {}".format(all_wb_num))
                        page_num = math.ceil(all_wb_num / 45)
                    except (IndexError, KeyError, AttributeError):
                        """这也是正常流程"""
                        continue
                if page_num and user_ident:
                    flag = 1
                    break
            if flag:
                break
            if count % 5 == 0:
                print("获取ident/page已经失败 {} 次，如失败次数过多请检查网络，或尝试更新cookies".format(count))
                time.sleep(3)
        return user_ident, page_num

    # def parse_img_list(self, img_info):
    #     # 解析图片列表
    #     img_url_base = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}"
    #     img_match = re.search(r":(\d+):(\w+):(\d+)", img_info)
    #     img_url = img_url_base.format(img_match.group(3), img_match.group(1), img_match.group(2))
    #     return img_url

    def deal_err(self, failure):

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

        yield failure.request

    def t_is_page_in_timerange(self, user_id, page):
        """
        该页是否在时间范围内
        :param user_id:
        :param page:
        :return:
        """
        result = "fine"
        first_part_url_base = "https://weibo.com/u/{}?page={}&is_all=1"
        sub_part_url_base = "https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100505&visible=0&is_all=1" \
                            "&profile_ftype=1&page={}&pagebar={}&pl_name=Pl_Official_MyProfileFeed__20" \
                            "&id=100505{}&script_uri=/{}/profile&feed_type=0&pre_page={}&domain_op=100505&__rnd={} "

        url1 = first_part_url_base.format(user_id, page)
        url3 = sub_part_url_base.format(page, 1, user_id, user_id, page, int(time.time() * 1000))

        if self.later_flag:
            p3_divs = []
            # 整页时间晚于规定时间范围，跳过该页
            count = 0
            # 获取idv
            while True:
                count += 1
                if count % 6 == 0:
                    print("重复5次失败，程序休眠30秒")
                    time.sleep(30)
                if count % 9 == 0:
                    print("获取page {} 最早微博时间失败8次，默认该页在时间范围内，在后续获取中进行处理".format(page))
                    return result
                p3_response = self.session_get(url3)
                try:
                    p3_html_text = json.loads(p3_response.text)["data"]
                    p3_divs = etree.HTML(p3_html_text).xpath("//div[@tbinfo]")
                except:
                    continue

                if p3_divs:
                    break

            if not self.t_is_divs_in_time_range(p3_divs, check_early=False, check_later=True):
                logging.info("page {} 时间晚于限定时间，跳过".format(page))
                result = "later"
            else:
                # 如果该条不晚于限定事件，把flag设为0，避免后面再次重复该部分请求
                self.later_flag = 0

        # 整页时间早于规定时间范围，直接结束循环
        if result == "fine":
            count = 0
            while True:
                if count % 3 == 0:
                    print("重复3次失败，程序休眠30秒")
                    time.sleep(30)
                if count % 6 == 0:
                    print("获取page{} 最早微博时间失败6次，默认该页在时间范围内，在后续获取中进行处理")
                    return result
                count += 1
                p1_response = self.session_get(url1)
                p1_divs = self.parse_div_from_part1_response(p1_response)
                if p1_divs:
                    break
            if not self.t_is_divs_in_time_range(p1_divs, check_early=True, check_later=False):
                logging.info("page {} 时间早于规定时间范围".format(page))
                result = "early"

        return result

    def t_is_divs_in_time_range(self, divs, check_early, check_later):
        """
        一组div是否在时间范围内
        这段别再动了，要梳逻辑的话对着这个梳 https://sm.ms/image/qCag3m4EuwT6hI2
        检查一组div是是否在时间范围内
        :param check_early: 是否要检查微博范围是否早于设定时间
        :param check_later: 是否要检查微博范围是否湾于设定时间
        :param divs: etree.HTML() 的divs
        :return:

        """
        result = True
        start_time = self.config["time_range"]["start_time"]
        stop_time = self.config["time_range"]["stop_time"]

        remark = ""

        # 整体（最晚的一条）是否比规定范围早
        if start_time and check_early:
            first_content = "".join(divs[0].xpath(".//div[@node-type='feed_list_content']//text()"))
            if "置顶" in first_content:
                newest_div = divs[1]
            else:
                newest_div = divs[0]

            wb_stop_time = int(newest_div.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])
            # 最晚的微博早于start_time,直接跳出循环
            if self.t_is_a_early_than_b(wb_stop_time, start_time, False):
                result = False
                remark = "wb stoptime {}, target start time {},divs too early. 该组div被过滤掉" \
                    .format(wb_stop_time, start_time)

        # 整体（最早的一条）是否比规定范围晚
        if stop_time and check_later:
            earliest_div = divs[-1]

            wb_start_time = int(earliest_div.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])
            if self.t_is_a_early_than_b(stop_time, wb_start_time, True):
                result = False
                remark = "target stop time {},wb start time {},to later. 该组div被过滤掉" \
                    .format(stop_time, wb_start_time)
        if not False:
            logging.info(remark)

        return result

    def t_is_time_in_range(self, time1):
        """
        判断单条微博时间（time1）是否在指定时间范围内
        包早不包晚
        :param time1: 毫秒时间戳(13位)或 "%Y-%m-%d %H:%M"格式的字符串
        :return:
        """
        start_time = self.config["time_range"]["start_time"]
        stop_time = self.config["time_range"]["stop_time"]
        if start_time and not self.t_is_a_early_than_b(start_time, time1, True):
            return False
        if stop_time and not self.t_is_a_early_than_b(time1, stop_time, False):
            return False
        return True

    def t_is_a_early_than_b(self, a, b, can_equal):
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
            timestamp_b = 0
            print("参数a应为int或str类型,返回0")
            return 0
        result = timestamp_b - timestamp_a
        if can_equal:
            return result >= 0
        else:
            return result > 0
