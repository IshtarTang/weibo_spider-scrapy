# coding=utf-8
import os
import requests
import json
import sys
import time
import traceback
import random


# ###################
#
#   放到wb_result.json同一路径，保存图片
#
# ##################
def read_json(file_name, coding="utf-8"):
    file1 = open(file_name, "r", encoding=coding).read()
    content = json.loads(file1)
    return content


def download_img(url, file_name, file_path):
    headers = {
        'Host': 'wx3.sinaimg.cn',
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Dest': 'image',
        'Referer': 'https://photo.weibo.com/',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    }
    try:
        response = requests.get(url, headers=headers)
        content = response.content
        with open(os.path.join(file_path, file_name), "wb") as op:
            op.write(content)
    except Exception as e:
        print(traceback.format_exc())
        print("{}下载失败".format(url))


def save_img(weibo_filepath, img_path, index, pic_class=None, ensure_ask=1):
    """
    :param weibo_filepath: 结果文件路径
    :param img_path: 图片存放路径
    :param index: 1保存result.json里的，2保存r_result.json里的
    :param pic_class:设了这项图片会保存到img_path/pic_class，不设的话，result.json的图保存在img_path/imgs，r_result.json保存在img_path/r_imgs
    :param ensure_ask: 默认在开始存图之前会停一下让你确认，输0就不用
    :return:
    """

    o_wb_result_filename = os.path.join(weibo_filepath, "wb_result.json")
    r_wb_result_filename = os.path.join(weibo_filepath, "r_wb_result.json")
    if not os.path.exists(r_wb_result_filename):
        print("r微博为简单获取")
        r_wb_result_filename = os.path.join(weibo_filepath, "sr_wb_result.json")

    # 1保存result.json里的,2保存r_result.json里的
    if index == "1" or index == 1:
        weibo_result_filename = o_wb_result_filename
    elif index == "2" or index == 2:
        weibo_result_filename = r_wb_result_filename
    else:
        print("序号错误，退出")
        time.sleep(3)
        sys.exit()

    # 指定了pic_class往pic_class存，没指定按微博类型存
    if pic_class is not None and isinstance(pic_class, str):
        img_path = os.path.join(img_path, pic_class)
    elif index == "1" or index == 1:
        img_path = os.path.join(img_path, "imgs")
    elif index == "2" or index == 2:
        img_path = os.path.join(img_path, "r_imgs")
    else:
        print("序号错误，退出")
        time.sleep(3)
        sys.exit()

    if not os.path.exists(weibo_result_filename):
        print("文件 {} 不存在，程序退出".format(weibo_result_filename))
        time.sleep(3)
        sys.exit()
    if not os.path.exists(img_path):
        os.makedirs(img_path)

    weibo_file = read_json(weibo_result_filename)
    img_urls_info = {}
    if index == 1 or index == "1":
        username = weibo_file[0]["user_name"]
        user_id = weibo_file[0]["user_id"]
        print(f"开始保存 {username}[{user_id}] 发布的图片")

    for weibo_info in weibo_file:
        bid = weibo_info["bid"]
        count = 1
        for img_url in weibo_info["img_list"]:
            # =================这里修改文件名和连接==============
            img_ident = bid + "_" + str(count)
            img_url = "https://wx3.sinaimg.cn/large/" + img_url.split("/")[-1] + ".jpg"
            img_urls_info[img_ident] = img_url
            count += 1

    # 读取已经下载好的图片
    downloaded_file = os.listdir(img_path)
    downloaded_file = list(map(lambda x: x.split(".")[0], downloaded_file))

    img_urls_info2 = {}
    print("读取中..")
    # 过滤已经下载完成的
    for img_ident in img_urls_info:
        if not img_ident in downloaded_file:
            img_urls_info2[img_ident] = img_urls_info[img_ident]
    print("读取到图片链接 {} 条，其中未下载的 {} 条".format(len(img_urls_info), len(img_urls_info2)))
    if ensure_ask:
        input("按回车继续")

    img_num = len(img_urls_info2)
    count = 0
    tmp_count = 0

    for img_ident in img_urls_info2:
        img_name = img_ident + ".jpg"
        url = img_urls_info[img_ident]
        download_img(url, img_name, img_path)
        count += 1
        print("保存进度 {}/{}，当前图片链接 {}".format(count, img_num, url))
        time.sleep(random.random() * 2)
        tmp_count += 1
        if tmp_count >= 10:
            time.sleep(2)
            tmp_count = 0
    print("保存完成")
    time.sleep(3)


if __name__ == '__main__':
    weibo_filepath = "."
    img_path = "."
    index = input("要保存哪个文件中的图片链接，保存result.json输入1，保存r_result.json输入2\n")
    save_img(weibo_filepath, img_path, index)
