# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
import json
import logging


class MyCountDownloaderMiddleware(object):
    def process_response(self, request, response, spider):
        """
        新版微博返回的json数据中有个{"ok":1}用来表示获取成功
        这个中间件用来检查ok是否为1，不为1会重新请求
        默认不检查，如果需要检查，在meta中加{"my_count": 0}
        """
        meta = request.meta
        my_count = meta.get("my_count", -1)
        # 不需检查
        if my_count == -1:
            return response

        j_data = json.loads(response.text)
        # 请求正常，无事发生
        if j_data["ok"] == 1:
            return response

        if my_count < 5:
            # 失败次数不超过5，+1重试
            request.meta["my_count"] += 1
            logging.info("{} 重新获取{}次".format(request.url, request.meta["my_count"]))
            print("{} 重新获取{}次".format(request.url, request.meta["my_count"]))
            return request
        else:
            if request.url == response.url:
                message = "{}：ok不为1，meta:{}，".format(request.url, meta)
            else:
                message = "{}：ok不为1，重定向至{}，meta:{}".format(request.url, response.url, meta)
            logging.error(message)
            print(message)
            raise IgnoreRequest  # 会去调用Request.errback


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
