# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
import json
import logging
import time
from spider_tool import comm_tool
from datetime import datetime
from twisted.internet import reactor, defer


class ResponseStatusHandlerMiddleware:

    def __init__(self, crawler):
        self.crawler = crawler
        self._paused = False

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if response.status == 414:
            if self._paused:
                return request.copy()
            else:
                self._paused = True
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}, {request.url} 请求频繁，爬取程序暂停5分钟"
                spider.logger.warning(f"{request.url} {message}")
                print(f"{request.url} {message}")
                self.crawler.engine.pause()

                def resume():
                    self._paused = False
                    self.crawler.engine.unpause()
                    print("爬取程序已恢复运行")
                    spider.logger.info("爬取程序已恢复运行")

                reactor.callLater(300, resume)
                return request.copy()

        return response


class LoginStatusMiddleware:
    def __init__(self, config_path, crawler):
        self.crawler = crawler
        config = json.load(open(config_path, "r", encoding="utf-8"))
        self.cookies = comm_tool.cookiestoDic(config["cookies_str"])

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('CONFIG_PATH'), crawler)

    def process_response(self, request, response, spider):
        """
        处理登录失效
        一般是程序中断一段时间后再运行，库里取出来的还是旧cookies
        更新cookies再重试就行
        :param request:
        :param response:
        :param spider:
        :return:
        """
        request_url = request.url
        response_url = response.url
        if ("passport" in response_url or "login" in response_url) and \
                ("passport" not in request_url and "login" not in request_url):
            retry_key = 'login_retry_count'
            retry_count = request.meta.get(retry_key, 0)

            if retry_count >= 1:
                spider.logger.error(f"[LoginStatus] 登录状态修复失败，请检查文件中的cookies是否过期")
                return response

            logging.warning(f"{request.url} cookies过期，使用文件中的cookies")
            new_request = request.copy()
            new_request.cookies = self.cookies
            new_request.meta[retry_key] = retry_count + 1

            return new_request
        return response


class JsonFieldRetryMiddleware:
    """
    检查返回的json里是否含有某个字段
    启用方式为在meta中设置{json_field_retry:[[k1],[k3,k4],...]}
    中间件会检查返回的json数据中是否有j_data[k1]和j_data[k3][k4]，只要缺失一个就会重试该请求
    """

    def __init__(self, max_retries=5):
        self.max_retries = max_retries

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            max_retries=crawler.settings.getint('JSON_FIELD_RETRY_MAX_RETRIES', 5)
        )

    def process_response(self, request, response, spider):
        json_field_retry = request.meta.get("json_field_retry", "")
        # 带这个配置才走这个中间件
        if not json_field_retry:
            return response

        try:
            j_data = json.loads(response.text)
        except Exception as e:
            spider.logger.warning(
                f"[JsonFieldRetry]:该请求未返回json格式数据，跳过该次字段检查\n请求连接：{request.url}\n响应连接：{response.url}\n{e}")
            return response

        extra_log = ""
        if request.callback == spider.get_mymblog_page:
            extra_log = "翻页结束"

        # 检查json数据中是否存在某字段且非空
        def field_exists(j_data, path: list):
            cur = j_data
            for key in path:
                if not isinstance(cur, dict) or key not in cur:
                    return False
                cur = cur[key]
            # 空值判定
            if cur in (None, '', [], {}):
                return False
            return True

        retry_count_key = "json_field_retry_count"
        for field_path in json_field_retry:
            # 检查是否有要求的字段，没有就检查请求重复次数，超过次数就放弃
            if not field_exists(j_data, field_path):
                retry_count = request.meta.get(retry_count_key, 0)
                if retry_count < self.max_retries:
                    spider.logger.warning(
                        f"[JsonFieldRetry]:字段缺失或空: {'.'.join(field_path)}，\n请求连接：{request.url}\n响应连接：{response.url}\n重试 {retry_count + 1}/{self.max_retries}")
                    new_request = request.copy()
                    new_request.meta[retry_count_key] = retry_count + 1
                    return new_request
                else:  # 重试几次还是没这个字段
                    allow_empty = request.meta.get("json_field_retry_allow_empty", False)
                    if allow_empty:
                        message = f"[JsonFieldRetry]字段缺失或空: {'.'.join(field_path)}，超过最大重试次数,但该请求标记为允许字段为空，将继续处理" \
                                  f"\n请求连接：{request.url}" \
                                  f"\n响应连接：{response.url}"
                        spider.logger.info(message)
                        print(message)
                    else:
                        message = f"[JsonFieldRetry] 字段缺失或空: {'.'.join(field_path)}，超过最大重试次数，放弃重试" \
                                  f"\n请求连接：{request.url}" \
                                  f"\n响应连接：{response.url}"
                        spider.logger.error(message)
                        print(message)
                    return response

        return response


class Ok1RetryMiddleware(object):

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        """
        新版微博返回的json数据中有个{"ok":1}用来表示获取成功
        这个中间件用来检查ok是否为1，不为1会重新请求
        在meta中设置{"ok1_retry": 0}启用该检查
        """
        meta = request.meta
        ok1_retry = meta.get("ok1_retry", -1)

        if ok1_retry == -1:  # 不启用该检查
            return response
        try:
            j_data = json.loads(response.text)
        except:
            # 带ok1_retry的请求正常返回的数据都是json格式，到这就是出了毛病被丢了个Html回来
            message = f"{response.url}解析内容出错，当前文本 {response.text}"
            spider.logger.error(message)
            print(message)
            return response

        data_ok = j_data.get("ok", "无该字段")

        if data_ok == 1:  # 请求正常，过
            return response
        else:  # 不行的都暂停一下重试
            if ok1_retry < 6:
                new_request = request.copy()
                new_request.meta["ok1_retry"] += 1

                message = f"[Ok1Retry]{request.url}响应中 ok={data_ok},已重新获取{request.meta['ok1_retry']}次"
                spider.logger.info(message)
                print(message)
                d = defer.Deferred()
                extra_delay = 5 if ok1_retry < 3 else 10
                reactor.callLater(extra_delay, d.callback, new_request)
                return d
            else:
                message = f"[Ok1Retry] 该链接ok校验失败超过最大重试次数，请求连接：{request.url}\n响应连接：{response.url}"
                spider.logger.warning(message)
                print(message)
                return response


class ScrapyWeibospiderSpiderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyWeibospiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader middleware.
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

        # 加cookies，不过现在换成正文里加了，要是正常就把这删了
        # config = json.load(open(config_path, encoding="utf-8"), encoding="utf-8")
        # cookies = config["cookies_str"]
        # request.cookies = comm_tool.cookiestoDic(cookies)
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
