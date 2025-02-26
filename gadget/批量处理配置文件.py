import json
import os
from pathlib import Path


def nodify_configs(changes: dict, folder_path=".", include_subfolders=0):
    """
    修改文件夹里所有配置文件
    :param changes: 要改的内容，k是配置项，v是值
    :param folder_path: 文件夹路径
    :param include_subfolders 0为只修改指定文件夹下的配置文件，1还会修改所有子文件夹里的配置文件
    :return: 改了哪些文件
    """
    filenames = get_all_config_path(folder_path, include_subfolders)
    for filename in filenames:
        # file_path = f"{folder_path}{os.sep}{filename}"
        info = json.load(open(filename, "r", encoding="utf-8"))
        for k, v in changes.items():
            info[k] = v
        json.dump(info, open(filename, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
        print("已修改", filename)
    return filenames


def get_all_config_path(path1=".", include_subfolders=0):
    """
    获取路径下的所有配置文件
    :param path1: 路径
    :param include_subfolders: 0为获取该文件夹里的配置文件，1还会包含所有子文件夹里的配置文件
    :return:
    """
    if include_subfolders:
        return [str(x) for x in Path(path1).rglob("*.json")]
    else:
        return [str(x) for x in Path(path1).glob("*.json")]


if __name__ == '__main__':
    changes = {
        "print_level": 1
    }  # {要改的配置项：要改成什么值}
    folder_path = "../auto_configs"  # 改该路径下所有配置文件
    nodify_configs(changes, folder_path, include_subfolders=1)
