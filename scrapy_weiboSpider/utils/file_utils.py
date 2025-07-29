import json
import os


def get_last_wb_public_time(wb_result_file_path):
    """
    :param wb_result_file_path: wb_result.json路径
    :return:文件里最晚一条微博
    """
    try:
        wbs = json.load(open(wb_result_file_path, "r", encoding="utf-8"))
        wbs_timestamp = [wb_info["public_timestamp"] for wb_info in wbs]
        return max(wbs_timestamp)
    except:
        return 0


def load_save_bid(saved_path):
    # saved_main_bid是打印用，只计算要爬的用户有多少微博，saved_all_bid是auto2模式去重用的
    save_main_bid = set()
    saved_all_bid = set()
    saved_wb_filepath = get_result_wb_filepath(saved_path)
    save_rwb_filepath = get_result_rwb_filepath(saved_path)
    if os.path.exists(saved_wb_filepath):
        saved_wb_data = json.load(open(saved_wb_filepath, "r", encoding="utf-8"))
        for wb_info in saved_wb_data:
            saved_all_bid.add(wb_info["bid"])
            save_main_bid.add(wb_info["bid"])

    if os.path.exists(save_rwb_filepath):
        saved_r_wb_data = json.load(open(save_rwb_filepath, "r", encoding="utf-8"))
        for r_wb_info in saved_r_wb_data:
            saved_all_bid.add(r_wb_info["bid"])
    return save_main_bid, saved_all_bid


def get_result_wb_filepath(saved_dir_path):
    return os.path.join(saved_dir_path, "wb_result.json")


def get_result_rwb_filepath(saved_dir_path):
    return os.path.join(saved_dir_path, "r_wb_result.json")
