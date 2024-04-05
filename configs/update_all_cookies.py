import os
import json


def update(configs_path, new_cookies_dir):
    """
    更新所有配置文件中的cookies
    :param configs_path: 放配置文件的文件夹路径
    :param new_cookies_dir: 新cookeis
    :return:
    """
    new_cookies_dir = new_cookies_dir.strip()
    file_list = os.listdir(configs_path)
    configs = filter(lambda x: ".json" in x, file_list)
    for config_filename in configs:
        config_path = "{}/{}".format(configs_path, config_filename)
        config = json.load(open(config_path, "r", encoding="utf-8"))
        config["cookies_str"] = new_cookies_dir
        json.dump(config, open(config_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)



# def update(new_cookies_str):
#     # 更新所有配置文件中的cookies
#     new_cookies_str = new_cookies_str.strip()
#     file_list = os.listdir("./")
#     configs = filter(lambda x: ".json" in x, file_list)
#     for config_path in configs:
#         config = json.load(open(config_path, "r", encoding="utf-8"))
#         config["cookies_str"] = new_cookies_str
#         json.dump(config, open(config_path, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
