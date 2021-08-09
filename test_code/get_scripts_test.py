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


user_id = ""
page = 1

config = read_json("../file/config.json")

session = requests.session()
session.headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"}
cookies_str = config["cookies_str"]
cookies = CookiestoDic(cookies_str)
session.cookies.update(cookies)

first_part_url_base = "https://weibo.com/u/{}?page={}&is_all=1"
first_part_url = first_part_url_base.format(user_id, page)
first_part_response = session.get(first_part_url)
parse = etree.HTML(first_part_response.content.decode("utf-8"))
script_eles = parse.xpath("//script")
scripts = []
for script_ele in script_eles:
    # script = script_ele.text
    script = etree.tostring(script_ele, encoding="utf-8").decode("utf-8").replace("&lt;", "<").replace("&gt;", ">")

    scripts.append(script)
divs = [1]

for script in scripts[-1::-1]:
    """
    这里容易出问题，改过了不过说不定还是会出
    """
    if 'class=\\"WB_feed' in script:
        re_s = re.search(r"\(({.*})\)", script.replace("\n", ""))
        try:
            html_text = json.loads(re_s.group(1))["html"]
            parse = etree.HTML(html_text)
            divs = parse.xpath("//div[@tbinfo]")
            if divs:
                print("fine")
                break
        except:
            continue

print(len(divs))
