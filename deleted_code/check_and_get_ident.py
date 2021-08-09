import json
import re
import os
import time
from lxml.html import etree
from scrapy.spiders import Request


# ���������������������ģ��õ���scrapy�����󣬵��������������Ӧ�ü�ʱ���ؽ����������requests

def check_and_get_ident(self, response):
    """
    ���������Ҫ��
    ����һ�����󣬼���Ƿ���������ȡ����ҳ�档��ȡ�û���ʶ������ȡ����ҳ���Ƿ���Ҫ�����ݡ�

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
            print("δ��ȡ��id,cookies������")
            os._exit(1)
    meta = response.meta
    meta["count"] += 1
    if user_name:
        # ������ȡ���û�������
        self.user_ident = "{}[{}]".format(user_name, response.meta["user_id"])
        self.test_list.append(user_name)

    else:
        # ʧ�������»�ȡ
        yield Request(meta["url"], callback=self.check_and_get_ident, cookies=self.cookies, meta=meta,
                      dont_filter=True, errback=self.deal_err)
