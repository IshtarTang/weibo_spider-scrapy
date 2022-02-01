# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy_weiboSpider.items import *
from scrapy_weiboSpider.settings import get_key_word
import json
import os
import logging


def log_and_print(text):
    logging.info(text)
    print(text)


class ScrapyWeibospiderPipeline(object):
    def open_spider(self, spider):
        print("文件准备")
        self.base_path = "./file"
        self.config = self.read_json(self.base_path + "/config.json", coding="gbk")
        self.filedir = self.get_get_filepath()
        self.pre_file_path = self.filedir + "/" + "prefile"
        # 过程文件路径
        self.weibo_filepath = self.pre_file_path + "/weibo.txt"
        self.rcomm_filepath = self.pre_file_path + "/rcomm.txt"
        self.ccomm_filepath = self.pre_file_path + "/ccomm.txt"
        self.simple_wb_info_fileapht = self.pre_file_path + "/simple_wb_info.json"
        # 结果文件路径
        self.wb_result_filepaht = self.filedir + "/wb_result.json"
        self.r_wb_result_filepaht = self.filedir + "/r_wb_result.json"

        # 初始化文件
        self.init_file()

        # 过程文件

        self.weibo_file = open(self.weibo_filepath, "a", encoding="utf-8")
        self.rcomm_file = open(self.rcomm_filepath, "a", encoding="utf-8")
        self.ccomm_file = open(self.ccomm_filepath, "a", encoding="utf-8")

        print("文件初始化完成")

    def process_item(self, item, spider):
        """
        会先暂存到中间文件
        :param item:
        :param spider:
        :return:
        """

        if isinstance(item, weiboItem):
            wb_dict = {
                "bid": item["bid"],
                "t_bid": item["t_bid"],
                "wb_url": item["wb_url"],
                "user_id": item["user_id"],
                "user_name": item["user_name"],
                "content": item["content"],
                "public_time": item["public_time"],
                "public_timestamp": item["public_timestamp"],
                "share_scope": item["share_scope"],
                "like_num": item["like_num"],
                "forward_num": item["forward_num"],
                "comment_num": item["comment_num"],
                "is_original": item["is_original"],
                "links": item["links"],
                "img_list": item["img_list"],
                "video_url": item["video_url"],
                "weibo_from": item["weibo_from"],
                "article_url": item["article_url"],
                "article_content": item["article_content"],
                "remark": item["remark"],
                "r_href": item["r_href"],
                "r_weibo": item["r_weibo"],

            }

            self.weibo_file.write(json.dumps(wb_dict, ensure_ascii=False) + "\n")
            return "wb {} 到暂存文件".format(item["wb_url"].split("?")[0])


        elif isinstance(item, commentItem):
            if item["comment_type"] == "root":
                superior_id = item["superior_id"].split("/")[2]
            else:
                superior_id = item["superior_id"]
            comm_dict = {
                "comment_type": item["comment_type"],
                "superior_id": superior_id,
                "comment_id": item["comment_id"],
                "content": item["content"],
                "user_name": item["user_name"],
                "user_url": item["user_url"],
                "date": item["date"],
                "like_num": item["like_num"],
                "img_url": item["img_url"],
                "link": item["link"]
            }

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
        # 关闭过程文件
        self.weibo_file.close()
        self.rcomm_file.close()
        self.ccomm_file.close()

        # 读取过程文件
        ccomms_str = open(self.ccomm_filepath, "r", encoding="utf-8").read()
        rcomms_str = open(self.rcomm_filepath, "r", encoding="utf-8").read()
        wb_str = open(self.weibo_filepath, "r", encoding="utf-8").read()
        if not wb_str:
            log_and_print("无微博，程序退出")
            return
        if ccomms_str:
            ccomm_dicts = [json.loads(str1) for str1 in ccomms_str.strip().split("\n")]
            ccomm_dicts = self.drop_duplicate(ccomm_dicts, "comment_id")
        else:
            ccomm_dicts = []

        if rcomms_str:
            rcomm_dicts = [json.loads(str1) for str1 in rcomms_str.strip().split("\n")]
            rcomm_dicts = self.drop_duplicate(rcomm_dicts, "comment_id")

        else:
            rcomm_dicts = []
        wb_dict = [json.loads(str1) for str1 in wb_str.strip().split("\n")]

        # 排序分组子评论
        ccomm_dicts = self.sort_dict(ccomm_dicts, "like_num", True)
        ccomm_dicts = self.classify_dicts(ccomm_dicts, "superior_id")

        # 排序根评论，将子评论插入，再分组
        rcomm_dicts = self.sort_dict(rcomm_dicts, "like_num", True)
        for rcomm in rcomm_dicts:
            # 如果存在子评论
            if ccomm_dicts.__contains__(rcomm["comment_id"]):
                rcomm["child_comm"] = ccomm_dicts[rcomm["comment_id"]]
            else:
                rcomm["child_comm"] = []
        rcomm_dicts = self.classify_dicts(rcomm_dicts, "superior_id")

        # 排序，将评论插入到微博中
        all_wb_dict = self.sort_dict(wb_dict, "public_timestamp", False)
        for wb in all_wb_dict:
            if rcomm_dicts.__contains__(wb["bid"]):
                wb["comments"] = rcomm_dicts[wb["bid"]]
            else:
                wb["comments"] = []
        # 结果文件
        wb_list = self.read_json(self.wb_result_filepaht)
        r_wb_list = self.read_json(self.r_wb_result_filepaht)
        # 将wb和r_wb分开
        for wb in all_wb_dict:
            if wb["t_bid"]:
                r_wb_list.append(wb)
            else:
                wb_list.append(wb)
        self.write_json(r_wb_list, self.r_wb_result_filepaht)

        # 读取之前的微博信息
        simple_wb_dict = self.read_json(self.simple_wb_info_fileapht)
        # 这里并不是为了分类，是为了把bid作为key提出来
        new_simple_wb_info = self.to_simple_info(all_wb_dict)
        # 将新的微博简单信息加进去
        simple_wb_dict.update(self.classify_dicts(new_simple_wb_info, "bid"))
        # 简单信息写入到文件
        self.write_json(simple_wb_dict, self.simple_wb_info_fileapht)

        for wb in wb_list:
            # 找源微博
            if wb["r_href"]:
                if wb["r_href"].split("/")[-1] in simple_wb_dict.keys():
                    simple_r_wb_info = simple_wb_dict[wb["r_href"].split("/")[-1]][0]
                    wb["r_weibo"] = simple_r_wb_info
                else:
                    wb["r_weibo"] = "源微博无法获取"
                    log_and_print("微博 {} 的源微博 {} 获取失败".format(wb["wb_url"], wb["r_href"]))
        wb_list = self.drop_duplicate(wb_list, "bid")

        # 微博写入到文件
        self.write_json(wb_list, self.wb_result_filepaht)

        # 清空临时文件
        input1 = input("\n文件保存完毕，是否清空临时文件（yes/no）")
        if input1 == "yes":
            log_and_print("清空临时文件")
            for t_filepaht in [self.weibo_filepath, self.rcomm_filepath, self.ccomm_filepath]:
                if os.path.exists(t_filepaht):
                    os.remove(t_filepaht)
                    log_and_print("删除文件 {}".format(t_filepaht))
        else:
            log_and_print("保留过程文件")
        log_and_print("保存结束，文件保存于{}\n程序正常退出".format(self.filedir))

    def get_get_filepath(self):
        key_word = get_key_word()
        path = self.base_path + "/" + key_word
        log_and_print("文件路径 {}".format(path))
        return path

    def init_file(self):
        # 文件目录和预写文件目录
        for path1 in [self.filedir, self.pre_file_path]:

            if not os.path.exists(path1):
                os.makedirs(path1)
                log_and_print("新建文件夹 {}".format(path1))
            else:
                log_and_print("文件夹 {} 已存在".format(path1))
        # 简单文件
        if not os.path.exists(self.simple_wb_info_fileapht):
            self.write_json({}, self.simple_wb_info_fileapht)
            log_and_print("新建文件 {}".format(self.simple_wb_info_fileapht))
        else:
            log_and_print("文件 {} 已存在".format(self.simple_wb_info_fileapht))
        # 两个结果文件
        for path1 in [self.wb_result_filepaht, self.r_wb_result_filepaht]:
            if not os.path.exists(path1):
                self.write_json([], path1)
                log_and_print("新建文件 {}".format(path1))
            else:
                log_and_print("文件 {} 已存在".format(path1))

    def write_json(self, file, path, coding="utf-8"):
        open(path, "w", encoding=coding).write(json.dumps(file, ensure_ascii=False, indent=4))

    def read_json(self, path, coding="utf-8"):
        str1 = open(path, "r", encoding=coding).read()
        json1 = json.loads(str1, encoding="utf-8")
        return json1

    def classify_dicts(self, dict_list, classify_key):
        """
        将dicts按某个key分类
        将 list[{k1:x1},{k1:x2},{k2:x3},{k2:x4}] 转为 {k1:[{k1:x1},{k1:x2}],k2:[{k2:x3},{k2:x3}]}
        :param dict_list:
        :param classify_key: 按哪个key分类
        :return:
        """
        classified_dict = {}
        for dict1 in dict_list:
            if not classified_dict.__contains__(dict1[classify_key]):
                classified_dict[dict1[classify_key]] = []
            classified_dict[dict1[classify_key]].append(dict1)
        return classified_dict

    def sort_dict(self, dicts: list, sort_by, reverse=False):
        """
        给一堆dict排序。一开始想到了pandas，不过试了下直接写的快一些
        :param dicts 列表，列表里是格式相同的字典
        :param sort_by: 按字典中的哪个值排序
        :param reverse: 默认升序
        :return:
        """
        s_dict = {}
        for dict1 in dicts:
            if not s_dict.__contains__(dict1[sort_by]):
                s_dict[dict1[sort_by]] = []
            s_dict[dict1[sort_by]].append(dict1)
        keys = sorted(s_dict.keys(), reverse=reverse)
        result_list = []
        for key in keys:
            result_list += s_dict[key]
        return result_list

    def to_simple_info(self, wbs):
        result_list = []
        for wb in wbs:
            simple_wb_info = {
                "user_name": wb["user_name"],
                "content": wb["content"],
                "bid": wb["bid"],
                "weibo_url": wb["wb_url"]
            }
            result_list.append(simple_wb_info)
        return result_list

    def drop_duplicate(self, dicts, d_key):
        d_dict = {}
        for dict1 in dicts:
            d_dict[dict1[d_key]] = dict1

        return [d_dict[key] for key in d_dict.keys()]
