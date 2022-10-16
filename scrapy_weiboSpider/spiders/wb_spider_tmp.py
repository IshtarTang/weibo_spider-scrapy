# -*- coding: utf-8 -*-
import scrapy
import os
from datetime import datetime
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
from scrapy_weiboSpider.settings import get_key_word
from scrapy_weiboSpider.config_path_file import config_path


def CookiestoDic(str1):
    result = {}
    cookies = str1.split(";")
    cookies_pattern = re.compile("(.*?)=(.*)")

    for cook in cookies:
        cook = cook.replace(" ", "")
        header_name = cookies_pattern.search(cook).group(1)
        header_value = (cookies_pattern.search(cook).group(2))
        result[header_name] = header_value

    return result


class WeiboSpiderSpider(scrapy.Spider):
    name = 'tmp_spider'
    allowed_domains = ['weibo.com']
    config = json.load(open(config_path, "r", encoding="utf-8"))
    key_word = get_key_word(config)
    saved_key = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'client-version': 'v2.36.7',
        'server-version': 'v2022.10.13.6',
        'X-XSRF-TOKEN': '1zUo_6x4BwvpdWnFzyTzpdPk',
        'traceparent': '00-a81bbd757576d56bea35803fa67aa670-88fd79556479dbf2-00',
        'Connection': 'keep-alive',
        'Referer': 'https://weibo.com/u/6591638928',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'TE': 'trailers',
    }

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": headers
    }
    cookies = CookiestoDic(config["cookies_str"])

    # 制造requests session
    session_start_time = time.time()
    session = requests.session()
    session.headers = headers
    session.cookies.update(cookies)

    def start(self):
        print("\n本次运行的文件key为 {}".format(self.key_word))
        comm_config_str = {"wb_rcomm": "微博根评论", "wb_ccomm": "微博子评论", "rwb_rcomm": "源微博根评论", "rwb_ccomm": "源微博子评论"}
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
        simple_wb_path = "./file" + "/" + self.key_word + "/prefile/simple_wb_info.json"
        per_wb_path = "./file" + "/" + self.key_word + "/prefile/weibo.txt"
        result_path = "./file" + "/" + self.key_word + "/wb_result.json"
        saved_key_config = self.config.get("deubg", {}).get("saved_key_file", "")
        if os.path.exists(simple_wb_path):
            if "swb" in saved_key_config or not saved_key_config:
                saved_wb1 = json.load(open(simple_wb_path, "r", encoding="utf-8"))
                self.saved_key += list(saved_wb1.keys())
                if saved_wb1:
                    print("录入 {} 的微博下载记录".format(simple_wb_path))
                else:
                    print("{} 无记录".format(simple_wb_path))

        if os.path.exists(result_path):
            if "wb" in saved_key_config or not saved_key_config:
                saved_wbs = json.load(open(result_path, "r", encoding="utf-8"))
                for wb in saved_wbs:
                    self.saved_key.append(wb["bid"])
                if saved_wbs:
                    print("录入 {} 的微博下载记录".format(simple_wb_path))
                else:
                    print("{} 无记录".format(simple_wb_path))
        if os.path.exists(per_wb_path):
            if "pwb" in saved_key_config or not saved_key_config:
                file1 = open(per_wb_path, "r", encoding="utf-8").read().strip()
                tmp_str = "[" + ",".join(file1.split("\n")) + "]"
                file = json.loads(tmp_str, encoding="utf-8")
                for x in file:
                    self.saved_key.append(x["bid"])
                if file:
                    print("录入 {} 的微博下载记录".format(simple_wb_path))
                else:
                    print("{} 无记录".format(simple_wb_path))

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
        self.user_id = self.config["user_id"]
        print("-----")
        start_url = "https://weibo.com/ajax/statuses/mymblog?" \
                    "uid={}&page={}&feature=0".format(self.user_id, 1)
        yield Request(start_url, callback=self.del_mymblog, cookies=self.cookies, headers=self.headers)

    def del_mymblog(self, response):
        page = int(response.request.url.split("page=")[1].split("&")[0])
        print("获取到page {} 页面，开始解析".format(page))
        content = response.text
        j_data = json.loads(content)

        since_id = j_data["data"]["since_id"]

        # open("z_{}.json".format(page), "w", encoding="utf-8").write(content)
        wb_list = j_data["data"]["list"]
        # 循环微博，解析
        for wb_info in wb_list:
            wb_item = weiboItem()

            bid = wb_info["mblogid"]
            wb_item["bid"] = bid

            user_id = wb_info["user"]["idstr"]
            wb_item["user_id"] = user_id

            wb_item["wb_url"] = "https://weibo.com/{}/{}".format(wb_item["bid"], wb_item["user_id"])
            wb_item["user_name"] = wb_info["user"]["screen_name"]
            html_text = wb_info["text_raw"]
            content_parse = etree.HTML(html_text)
            content = "\n".join(content_parse.xpath("//text()"))
            wb_item["content"] = content

            created_at = wb_info["created_at"]
            create_datetime = datetime.strptime(created_at, '%a %b %d %X %z %Y')
            create_time = datetime.strftime(create_datetime, "%Y-%m-%d %H:%M")
            wb_item["public_time"] = create_time

            wb_item["public_timestamp"] = int(time.mktime(create_datetime.timetuple()) * 1000)
            wb_item["share_scope"] = "暂略"
            wb_item["like_num"] = wb_info["attitudes_count"]
            wb_item["forward_num"] = wb_info["reposts_count"]
            wb_item["comment_num"] = wb_info["comments_count"]
            share_repost_type = wb_info["share_repost_type"]
            wb_item["is_original"] = 0 if share_repost_type else 1
            wb_item["weibo_from"] = wb_info["source"]

            img_list = []
            mid = wb_info["mid"]
            pic_ids = wb_info["pic_ids"]
            wimg_url_base = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}"

            for pid in pic_ids:
                wimg_url = wimg_url_base.format(user_id, mid, pid)
                img_list.append(wimg_url)
            wb_item["img_list"] = img_list

            # ##############在修
            if wb_info["comments_count"]:
                pass

            links = []
            if wb_info.get("url_struct", []):
                for url_info in wb_info["url_struct"]:
                    links.append(url_info["ori_url"])
            wb_item["links"] = links

            # 应该不用写
            try:
                if wb_info.get("retweeted_status", 0):
                    r_href = "/{}/{}".format(wb_info["retweeted_status"]["user"]["idstr"],
                                             wb_info["retweeted_status"]["mblogid"])
                else:
                    r_href = ""
            except Exception as e:
                r_href = ""

            wb_item["t_bid"] = ""
            wb_item["r_href"] = r_href
            wb_item["r_weibo"] = {}
            wb_item["remark"] = ""
            wb_item["video_url"] = ""
            wb_item["article_url"] = ""
            wb_item["article_content"] = ""

            text_len = wb_info["textLength"]
            # 字数超过的送到获取长文的地方去，原content会被覆盖
            if text_len < 240:
                yield wb_item
            else:
                longtext_url = "https://weibo.com/ajax/statuses/longtext?id={}".format(bid)
                yield Request(longtext_url, callback=self.get_long_text,
                              cookies=self.cookies, headers=self.headers,
                              meta={"wb_item": wb_item, "count": 0})

        if since_id and page < 10:
            next_url = "https://weibo.com/ajax/statuses/mymblog?" \
                       "uid={}&page={}&feature=0&since_id={}".format(self.user_id, page + 1, since_id)
            yield Request(next_url, callback=self.del_mymblog, cookies=self.cookies, headers=self.headers)
        else:
            print("最后一页{} 没页数了".format(page))

    def get_long_text(self, response):
        content = response.text
        j_data = json.loads(content)
        # print(j_data)
        meta = response.meta
        meta["count"] += 1
        wb_item = meta["wb_item"]

        if j_data["ok"] and j_data["data"]:
            # 确实是长微博
            if j_data["data"]:
                content = j_data["data"]["longTextContent"]
                wb_item["content"] = content
            yield wb_item
        elif j_data["ok"]:
            # 判断是否长微博是用长度判断的，可能出现误判，获取长文本未返回数据
            # 这种情况直接用之前的短文本就行
            yield wb_item
        elif meta["count"] < 3:
            # 获取失败，再试试
            yield Request(response.request.url, callback=self.get_long_text,
                          cookies=self.cookies, headers=self.headers,
                          meta=meta)
        else:
            logging.warning("{} 长文获取失败")

    def get_ident_and_page_num(self):
        pass

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
