# -*- coding: utf-8 -*-

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# # See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy_weiboSpider.items import *
from spider_tool.comm_tool import get_result_filepath
import json
import os
import logging
from scrapy_weiboSpider.config_path_file import config_path
from spider_tool import merge_wb


def log_and_print(text):
    logging.info(text)
    print(text)


class NewVerPipeline(object):
    def __init__(self):
        pass

    def open_spider(self, spider):
        pass

    def process_item(self, item: scrapy.Item, spider):
        pass

    def close_spider(self, spider):
        pass


class ScrapyWeibospiderPipeline(object):
    def __init__(self):
        print("文件准备")
        self.config = json.load(open(config_path, "r", encoding="utf-8"))
        self.filedir = get_result_filepath(self.config)
        self.pre_file_path = self.filedir + "/" + "prefile"
        # 文件路径
        self.weibo_filepath = self.pre_file_path + "/weibo.txt"
        self.rcomm_filepath = self.pre_file_path + "/rcomm.txt"
        self.ccomm_filepath = self.pre_file_path + "/ccomm.txt"

        # 初始化文件
        for path1 in [self.filedir, self.pre_file_path]:
            if not os.path.exists(path1):
                os.makedirs(path1)
                log_and_print("新建文件夹 {}".format(path1))
            else:
                log_and_print("文件夹 {} 已存在".format(path1))

        # 过程文件
        self.weibo_file = None
        self.rcomm_file = None
        self.ccomm_file = None

        print("文件初始化完成")

    def open_spider(self, spider):
        # 打开过程文件
        self.weibo_file = open(self.weibo_filepath, "a", encoding="utf-8")
        self.rcomm_file = open(self.rcomm_filepath, "a", encoding="utf-8")
        self.ccomm_file = open(self.ccomm_filepath, "a", encoding="utf-8")

    def process_item(self, item: scrapy.Item, spider):
        """
        写文件，一个item一行，不做过多处理
        :param item:
        :param spider:
        :return:
        """
        if isinstance(item, weiboItem):
            wb_dict = dict(item)

            self.weibo_file.write(json.dumps(wb_dict, ensure_ascii=False) + "\n")
            return "wb {} 到暂存文件".format(item["wb_url"].split("?")[0])

        elif isinstance(item, commentItem):
            if item["comment_type"] == "root":
                item["superior_id"] = item["superior_id"].split("/")[2]
            comm_dict = dict(item)

            if item["comment_type"] == "root":
                self.rcomm_file.write(json.dumps(comm_dict, ensure_ascii=False) + "\n")
                return "r comm {} id[{}] superior_id[{}]".format(
                    item["content"], item["comment_id"], item["superior_id"])
            else:
                self.ccomm_file.write(json.dumps(comm_dict, ensure_ascii=False) + "\n")
                return "c comm {} id[{}] superior_id[{}]".format(
                    item["content"], item["comment_id"], item["superior_id"])
        else:
            return "item notype {}".format(item)

    def close_spider(self, spider):
        logging.info("文件整合开始")
        # 关闭写文件
        self.weibo_file.close()
        self.rcomm_file.close()
        self.ccomm_file.close()

        user_id = self.config["user_id"]
        # 主要整理是调用了方法
        merge_wb_file = merge_wb.MergeWbFile(
            self.filedir, user_id, self.config.get("get_rwb_detail", 1), self.config.get("ensure_ask", 1))
        merge_wb_file.run()
