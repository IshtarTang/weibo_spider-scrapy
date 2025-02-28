import json
from pathlib import Path
import save_img_new
import os
from spider_tool import comm_tool
import 批量处理配置文件


def get_weibo_file_dir(path1=".", include_subfolders=0):
    """
    获取路径下的所有配置文件
    :param path1: 路径
    :param include_subfolders: 0为获取该文件夹里的配置文件，1还会包含所有子文件夹里的配置文件
    :return:
    """
    if include_subfolders:
        return [str(x) for x in Path(path1).rglob("*")]
    else:
        return [str(x) for x in Path(path1).glob("*")]


def get_weibo_file_from_config(dir, relative_path=""):
    """
    :param dir: 放配置文件的路径
    :param relative_path: 当前程序的运行路径相对scrapy运行时的路径（结果文件是按scrapy运行路径存的）
    :return:
    """
    config_paths = 批量处理配置文件.get_config_paths(dir, 1)
    result_filepaths = []
    for config_path in config_paths:
        config = json.load(open(config_path, "r", encoding="utf-8"))
        result_filepath = comm_tool.get_result_filepath(config)
        result_filepaths.append(os.path.join(relative_path,result_filepath))
    return result_filepaths


if __name__ == '__main__':
    # 图片存哪
    result_filepath = f"E:{os.sep}wb_imgs"

    # 1 和 2 选一种来指定下啥

    # 1 下载文件夹里所有配置的结果文件的图片
    # 指定放config的文件夹
    configs_path = f"..{os.sep}auto_configs"
    weibo_filepaths = get_weibo_file_from_config(configs_path, "..")
    # 2 下载文件夹里所有结果文件的图片
    # 直接指定放结果文件的文件夹
    # weibo_files_path = f"..{os.sep}auto_file"
    # weibo_filepaths = get_weibo_file_dir(weibo_files_path)

    # -----------------------------------
    for weibo_filepath in weibo_filepaths:
        imgs_path = os.path.join(result_filepath, os.path.basename(weibo_filepath))
        save_img_new.save_img(weibo_filepath, imgs_path,index="1",pic_class="", ensure_ask=0)
