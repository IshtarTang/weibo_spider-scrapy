import requests
import json
import os
from lxml.html import etree
from tool import cookiestodic, write_file
from selenium import webdriver


def get_driver(headers, cookies):
    options = webdriver.ChromeOptions()
    # 无界面
    options.add_argument('--headless')
    # 请求头
    for header_key in headers:
        options.add_argument('{}="{}"'.format(header_key, headers[header_key]))
    driver = webdriver.Chrome("chromedriver.exe", options=options)  # Chrome浏览器
    # 加域名（加cookeis前先把域名访问下）
    driver.get("https://weibo.com")
    # 加cookies
    for cookie in cookies:
        driver.add_cookie({"name": cookie, "value": cookies[cookie], "path": "/", "domain": "weibo.com"})
    # 刷新，返回
    driver.refresh()
    return driver


def main():
    # 临时写的下图的
    file = json.load(open("wb_result.json", "r", encoding="utf-8"))
    imgs_info = []
    # file = file[:100]
    # 给图片标文件名
    for wb in file:
        index = 1
        for img_url in wb["img_list"]:
            img_info = {}
            iid = wb["bid"] + "_" + str(index)
            index += 1
            img_info["file_id"] = iid
            img_info["img_url"] = img_url
            imgs_info.append(img_info)

    session = requests.session()
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'sec-ch-ua': '^\\^Chromium^\\^;v=^\\^106^\\^, ^\\^Google',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '^\\^Windows^\\^',
    }
    img_headers = headers = {
        'authority': 'wx3.sinaimg.cn',
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://photo.weibo.com/',
        'sec-ch-ua': '^\\^Chromium^\\^;v=^\\^106^\\^, ^\\^Google',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '^\\^Windows^\\^',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    }
    session.headers = img_headers

    # cookies_str = "SINAGLOBAL=9660189142619.871.1625547924755; UOR=,,login.sina.com.cn; XSRF-TOKEN=dzrgnFnmXoKBhzM-w1rDJxmQ; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFlK8wHn55LiDCvTD8mF1.n5JpX5KzhUgL.Fo2NShnpe0Bce0z2dJLoIpXXeCH8SC-RxbHFSEH8SE-RBEHWBbH8SE-RBEHWBntt; SSOLoginState=1668297245; SCF=AgQL8ho8S9VCgxHBFSlHE6KWEaQJeYzc4ESBw87Pq7JKnPCYIQNfQb6txdI9pW_-uUMycGnxXrBDIvlMUFht1tw.; SUB=_2A25OdEI-DeRhGedJ71oQ8yrKyD6IHXVtADT2rDV8PUNbmtANLVH_kW9NUeseWgDghlD-SKXx5BVW5rkf_igDiSfR; ALF=1699833325; wvr=6; _s_tentry=weibo.com; Apache=4721973954849.736.1668302406073; ULV=1668302406099:492:3:2:4721973954849.736.1668302406073:1668286345308; wb_view_log_1748134632=1536*8641.25; WBPSESS=Dt2hbAUaXfkVprjyrAZT_BKQaavUhojE1XasYTHsBSO7274zFCBvqhYmi5iBVAt2mOLFM5Z-EoJ4yQkqOTL08tls1Jdi-keVh7s3vGYqSz-bN0ABrFEusAn7jOQV8AZifmwMQvw5AP9TEjpFUG1c4KuL8WZq_H_ILzBbW7E0UYhK5OHNWMZdHlhexTbd8O076fD5P8RPSD3FcJUtZFhdTw==; PC_TOKEN=d9b6b1b19f; webim_unReadCount=%7B%22time%22%3A1668324520926%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A2%7D"
    cookies_str = "SINAGLOBAL=9660189142619.871.1625547924755; UOR=,,login.sina.com.cn; wb_timefeed_1748134632=1; SSOLoginState=1672587813; _s_tentry=login.sina.com.cn; Apache=5391419156448.824.1672587817941; ULV=1672587817958:502:1:1:5391419156448.824.1672587817941:1672398468416; wvr=6; wb_view_log_1748134632=1536*8641.25; SCF=AgQL8ho8S9VCgxHBFSlHE6KWEaQJeYzc4ESBw87Pq7JKSQ2JGKPi1L8fU2oyRjbSc7npLfRZsqWhZs8VSRbsOrU.; SUB=_2A25OssUNDeRhGedJ71oQ8yrKyD6IHXVtybHFrDV8PUJbmtAKLVbkkW9NUeseWgKSduLjACCxgpNb9RUwDhX-q_lo; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFlK8wHn55LiDCvTD8mF1.n5JpX5K-hUgL.Fo2NShnpe0Bce0z2dJLoIpXXeCH8SC-RxbHFSEH8SE-RBEHWBbH8SE-RBEHWBntt; ALF=1675504254; webim_unReadCount=%7B%22time%22%3A1672923163629%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A2%7D; PC_TOKEN=ad9e71a149"
    cookies = cookiestodic(cookies_str)
    requests.utils.add_dict_to_cookiejar(session.cookies, cookies)
    driver = get_driver(headers, cookies)
    schedule_filepath = "img_schedule.json"
    if os.path.exists(schedule_filepath):
  
        schedule = json.load(open(schedule_filepath, "r", encoding="utf-8"))
        count = schedule["done"]
    else:
        count = 0
        schedule = {"done": 0}

    for img_info in imgs_info[schedule["done"]:]:
        url = img_info["img_url"]
        driver.get(url)
        try:
            r_img_url = driver.find_element("xpath", "//img").get_attribute("src")
        except:
            print("异常", img_info)
            continue
        pic_type = r_img_url.split(".")[-1]
        filename = img_info["file_id"] + "." + pic_type
        # r_img_url=r_img_url.replace("large","mw690")
        r_img_response = session.get(r_img_url)
        pic = r_img_response.content
        with open("img/" + filename, "wb") as op:
            op.write(pic)
        count += 1
        if count % 20 == 0 or count == len(imgs_info):
            schedule = {"done": count}
            json.dump(schedule, open(schedule_filepath, "w", encoding="utf-8"))

        print("{} 保存完毕，进度{}/{}".format(filename, count, len(imgs_info)))

    print("所有图片保存完毕，清除进度文件")
    if os.path.exists(schedule_filepath):
        os.remove(schedule_filepath)


if __name__ == '__main__':
    main()
