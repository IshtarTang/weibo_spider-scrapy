import json
import re
import os
import time
from lxml.html import etree
from scrapy.spiders import Request


# 这个方法是用来做请求检查的，用的是scrapy的请求，但是想想这个方法应该即时返回结果，改用了requests

def check_and_get_ident(self, response):
    """
    这个方法还要改
    进行一次请求，检查是否能正常获取到到页面。获取用户标识，检查获取到的页面是否有要的内容。

    :param response:
    :return:
    """
    user_name = ""
    scripts = response.xpath("//script")
    re_s = re.search(r"\(({.*})\)", scripts.extract()[-1])
    open("./test_code.html", "w", encoding="utf-8").write(scripts.extract()[-1])
    try:
        html_text = json.loads(re_s.group(1))["html"]
        parse = etree.HTML(html_text)
        user_name = parse.xpath("//div[contains(@class,'WB_info')]/a/text()")[0]
    except:
        if response.meta["count"] > 10 and not self.user_ident:
            time.sleep(6)
            print("未获取到id,cookies有问题")
            os._exit(1)
    meta = response.meta
    meta["count"] += 1
    if user_name:
        # 正常获取到用户名就设
        self.user_ident = "{}[{}]".format(user_name, response.meta["user_id"])
        self.test_list.append(user_name)

    else:
        # 失败则重新获取
        yield Request(meta["url"], callback=self.check_and_get_ident, cookies=self.cookies, meta=meta,
                      dont_filter=True, errback=self.deal_err)
