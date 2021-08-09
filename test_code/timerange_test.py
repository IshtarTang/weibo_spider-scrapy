# coding=utf-8
import json
import requests
from lxml.html import etree
import re
import time


def is_a_early_than_b(a, b, can_equal):
    """
    时间比较
    :param a: 毫秒时间戳(13位)或 "%Y-%m-%d %H:%M"格式的字符串
    :param b: 毫秒时间戳(13位)或 "%Y-%m-%d %H:%M"格式的字符串
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


def CookiestoDic(str):
    result = {}
    cookies = str.split(";")
    # print(cooks)
    cookies_pattern = re.compile("(.*?)=(.*)")

    for cook in cookies:
        # print(cook)
        cook = cook.replace(" ", "")
        header_name = cookies_pattern.search(cook).group(1)
        header_value = (cookies_pattern.search(cook).group(2))
        result[header_name] = header_value

    return result


def read_json(file_name, coding="utf-8"):
    file1 = open(file_name, "r", encoding=coding).read()
    content = json.loads(file1)

    return content


def write_test(file, filename="./test_code.html", coding="utf-8"):
    open(filename, "w", encoding=coding).write(file)


def get_div3():
    test_list = []
    config = read_json("../file/config.json")

    # 一个requests的session，在解析部分有需要立刻返回结果的请求
    cookies = CookiestoDic(config["cookies_str"])
    session = requests.session()
    session.headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"}
    session.cookies.update(cookies)

    sub_part_url_base = "https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100505&visible=0&is_all=1" \
                        "&profile_ftype=1&page={}&pagebar={}&pl_name=Pl_Official_MyProfileFeed__20" \
                        "&id=100505{}&script_uri=/{}/profile&feed_type=0&pre_page={}&domain_op=100505&__rnd={} "

    page = 1
    user_id = ""
    url3 = sub_part_url_base.format(page, 1, user_id, user_id, page, int(time.time() * 1000))
    print(session.cookies)
    p3_response = session.get(url3)
    write_test(p3_response.text)
    p3_html_text = json.loads(p3_response.text)["data"]
    p3_divs = etree.HTML(p3_html_text).xpath("//div[@tbinfo]")

    return p3_divs


def is_divs_in_time_range(divs, check_early, check_later):
    """
    这段别再动了，要梳逻辑的话对着这个梳 https://sm.ms/image/qCag3m4EuwT6hI2

    检查一组div是是否在时间范围内
    :param divs: etree.HTML() 的divs
    :return:

    """
    result = True
    config = read_json("../file/config.json")
    start_time = config["personal_homepage_config"]["time_range"]["start_time"]
    stop_time = config["personal_homepage_config"]["time_range"]["stop_time"]
    wb_stop_time = ""
    wb_start_time = ""

    if (start_time and stop_time) and not stop_time - start_time > 0:
        print("时间范围设定错误（开始时间晚于结束时间）")
        return False

    # 整体（最晚的一条）是否比规定范围早
    if start_time and check_early:
        first_content = "".join(divs[0].xpath(".//div[@node-type='feed_list_content']//text()"))
        if "置顶" in first_content:
            newest_div = divs[1]
        else:
            newest_div = divs[0]

        wb_stop_time = int(newest_div.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])
        # 最晚的微博早于start_time,直接跳出循环
        if is_a_early_than_b(wb_stop_time, start_time, False):
            print("早了")
            result = False

    # 整体（最早的一条）是否比规定范围晚
    if stop_time and check_later:

        earliest_div = divs[-1]

        wb_start_time = int(earliest_div.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])
        if is_a_early_than_b(stop_time, wb_start_time, True):
            print("晚了")
            result = False
    print("0 wb stop {}".format(wb_stop_time))
    print("start {}".format(start_time))
    print()
    print("-1 wb start {}".format(wb_start_time))
    print("stop {}".format(stop_time))
    return result


if __name__ == '__main__':
    divs3 = get_div3()
    print(len(divs3))
    result1 = is_divs_in_time_range(divs3, True, True)
