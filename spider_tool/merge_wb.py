import json
import logging
import os
import pandas as pd


# 用来做结果文件聚合的，在piplines里有一次调用，也可以单独跑


def log_and_print(text):
    logging.info(text)
    print(text)


class MergeWbFile:
    def __init__(self, filedir, main_user_id, is_simple_r_wb=0, ensure_ask=1):
        """

        :param filedir: 爬虫结果文件的路径，从项目路径开始算的相对路径
        :param main_user_id: 爬的谁的主页，用来区分是不是被转发的别人的微博
        :param is_simple_r_wb: 被转发的源微博是否只获取简单内容，详细源微博和简单源微博结果文件路径不同
        :param ensure_ask 设成1会问要不要保留过程文件，设成0就不问，自动保留
        """
        self.ensure_ask = ensure_ask
        self.main_user_id = main_user_id
        self.filedir = filedir
        self.pre_file_path = self.filedir + "/" + "prefile"
        # 爬虫文件路径
        self.weibo_filepath = self.pre_file_path + "/weibo.txt"
        self.rcomm_filepath = self.pre_file_path + "/rcomm.txt"
        self.ccomm_filepath = self.pre_file_path + "/ccomm.txt"
        # 结果文件路径
        self.wb_result_filepaht = self.filedir + "/wb_result.json"
        if is_simple_r_wb:
            self.r_wb_result_filepaht = self.filedir + "/r_wb_result.json"
        else:
            self.r_wb_result_filepaht = self.filedir + "/sr_wb_result.json"

    def drop_duplication_all(self):
        # 去除完全重复的行，并且写回去，如果是bid相同但有些内容(比如点赞数)不同不用处理，新旧版本数据都保留
        # 不用set因为不能乱序
        for path1 in [self.weibo_filepath, self.rcomm_filepath, self.ccomm_filepath]:
            with open(path1, "r", encoding="utf-8") as op:
                lines = op.read().split("\n")
            df = pd.DataFrame(lines)
            df.drop_duplicates(inplace=True)
            new_lines = df[0].values.tolist()
            with open(path1, "w", encoding="utf-8") as op:
                op.write("\n".join(new_lines))

    def run(self):
        """
        流程
        先把prefile文件按行做一个去重,只去完全重复的行
        把prefile文件读出来,评论按点赞排,微博按时间排
        子评论插父评论里,父评论插微博里

        :return:
        """
        logging.info("文件整合开始")
        self.drop_duplication_all()  # prefile去重

        # 读取过程文件
        ccomms_str = open(self.ccomm_filepath, "r", encoding="utf-8").read()
        rcomms_str: str = open(self.rcomm_filepath, "r", encoding="utf-8").read()
        wb_str = open(self.weibo_filepath, "r", encoding="utf-8").read()

        if not wb_str:
            log_and_print("无微博，程序退出")
            return
        # 全部读成json
        if ccomms_str:
            ccomm_dicts = [json.loads(str1) for str1 in ccomms_str.strip().split("\n")]
            ccomm_dicts = drop_duplicate(ccomm_dicts, "comment_id", print_info="ccomm")
        else:
            ccomm_dicts = []

        if rcomms_str:
            rcomm_dicts = [json.loads(str1) for str1 in rcomms_str.strip().split("\n")]
            rcomm_dicts = drop_duplicate(rcomm_dicts, "comment_id", print_info="rcomm")
        else:
            rcomm_dicts = []

        wb_dict = [json.loads(str1) for str1 in wb_str.strip().split("\n")]
        wb_dict = drop_duplicate(wb_dict, "bid", print_info="weibo")
        # 排序子评论,按父评论分组
        ccomm_dicts = sort_dict(ccomm_dicts, "like_num", True)
        ccomm_dicts = classify_dicts(ccomm_dicts, "superior_id", print_info="ccomm")

        # 排序根评论，将子评论插入，按微博分组
        rcomm_dicts = sort_dict(rcomm_dicts, "like_num", True, print_info="rcomm")
        for rcomm in rcomm_dicts:
            # 如果存在子评论
            if ccomm_dicts.__contains__(rcomm["comment_id"]):
                rcomm["child_comm"] = ccomm_dicts[rcomm["comment_id"]]
            else:
                rcomm["child_comm"] = []
        rcomm_dicts = classify_dicts(rcomm_dicts, "superior_id", print_info="rcomm")

        # 微博按时间排序
        all_wb_dict = sort_dict(wb_dict, "public_timestamp", False, print_info="weibo")
        # 将评论插入到微博中
        for wb in all_wb_dict:
            if rcomm_dicts.__contains__(wb["bid"]):
                wb["comments"] = rcomm_dicts[wb["bid"]]
            else:
                wb["comments"] = []
        # 结果文件
        wb_list = []
        r_wb_list = []
        # 将wb和r_wb分开
        for wb in all_wb_dict:
            if wb["user_id"] == self.main_user_id:
                wb_list.append(wb)
            else:
                r_wb_list.append(wb)

        # 源微博写文件
        write_json(r_wb_list, self.r_wb_result_filepaht)

        # 取部分字段，放到wb的rwb里
        new_simple_wb_info = to_simple_info(all_wb_dict)
        # 这里并不是为了分类，是为了把bid作为key提出来
        simple_wb_dict = classify_dicts(new_simple_wb_info, "bid")

        for wb in wb_list:
            # 找源微博
            if wb["r_href"]:
                if wb["r_href"].split("/")[-1] in simple_wb_dict.keys():
                    simple_r_wb_info = simple_wb_dict[wb["r_href"].split("/")[-1]][0]
                    wb["r_weibo"] = simple_r_wb_info
                else:
                    wb["r_weibo"] = "源微博无法获取"
                    log_and_print("微博 {} 的源微博 {} 获取失败".format(wb["wb_url"], wb["r_href"]))

        # 微博写入到文件
        write_json(wb_list, self.wb_result_filepaht)
        logging.info("整合完成")
        logging.info("共计微博{}条".format(len(wb_list)))
        print("\n文件保存完毕，共计微博{}条".format(len(wb_list)))
        # 清空临时文件
        if self.ensure_ask:
            input1 = input("是否清空临时文件（yes/no）")

            if input1 == "yes":
                log_and_print("清空临时文件")
                for t_filepaht in [self.weibo_filepath, self.rcomm_filepath, self.ccomm_filepath]:
                    if os.path.exists(t_filepaht):
                        os.remove(t_filepaht)
                        log_and_print("删除文件 {}".format(t_filepaht))
            else:
                log_and_print("保留过程文件")
        else:
            log_and_print("保留过程文件")

        log_and_print("保存结束，文件保存于{}\n程序正常退出".format(self.filedir))

    def init_file(self):
        # 文件目录和预写文件目录
        for path1 in [self.filedir, self.pre_file_path]:

            if not os.path.exists(path1):
                os.makedirs(path1)
                log_and_print("新建文件夹 {}".format(path1))
            else:
                log_and_print("文件夹 {} 已存在".format(path1))
        # 两个结果文件
        for path1 in [self.wb_result_filepaht, self.r_wb_result_filepaht]:
            if not os.path.exists(path1):
                write_json([], path1)
                log_and_print("新建文件 {}".format(path1))
            else:
                log_and_print("文件 {} 已存在".format(path1))


def write_json(json_obj, path, coding="utf-8"):
    open(path, "w", encoding=coding).write(json.dumps(json_obj, ensure_ascii=False, indent=4))


def read_json(path, coding="utf-8"):
    str1 = open(path, "r", encoding=coding).read()
    json_obj = json.loads(str1, encoding="utf-8")
    return json_obj


def classify_dicts(dict_list, classify_key, print_info=""):
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
    if print_info:
        print(f"done: 分类 {print_info}")
    return classified_dict


def sort_dict(dicts, sort_by, reverse=False, print_info=""):
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
    if print_info:
        print(f"done: 排序 {print_info}")
    return result_list


def to_simple_info(wbs):
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


def drop_duplicate(dicts: list, d_key, print_info=""):
    """
    对一堆dict去重，两个dict下d_key的值相同则视为两个dict相同
    :param dicts: 一个list，list中为dict
    :param d_key: 按dict哪个key的值去重
    :return:
    """
    f_dict = {}  # {d_key的值：dict}，
    for current_dict in dicts:
        # 如果两个dict的d_key的值相同，那么数据量大的会把数据量小的覆盖掉,一样长的话保留后来的
        current_d_value = current_dict[d_key]
        if f_dict.get(current_d_value, ""):
            old_dict = f_dict[current_d_value]
            # 对比两dict的长度
            if len(str(old_dict)) <= len(str(current_dict)):
                f_dict[current_d_value] = current_dict
                logging.debug(f"mewge_wb.py  过滤 {old_dict}")
            else:
                logging.debug(f"mewge_wb.py  过滤 {current_dict}")

        else:
            f_dict[current_d_value] = current_dict
    if print_info:
        print(f"done: 去重 {print_info}")
    return [f_dict[key] for key in f_dict.keys()]
