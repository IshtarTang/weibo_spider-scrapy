from lxml.html import etree
import requests
import re
import json


def read_json(file_name, coding="utf-8"):
    file1 = open(file_name, "r", encoding=coding).read()
    content = json.loads(file1)

    return content


def write_test(file, filename="./test_code.html", coding="utf-8"):
    open(filename, "w", encoding=coding).write(file)



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

x = read_json("./file/wb_1_1748134632[1627920000000-0]/wb_result.json")
print(len(x))


