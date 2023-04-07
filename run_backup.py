import os
import json
import msvcrt


# 总之就是会把cf_list里的配置全爬一遍


def run_all(configs_path, config_list):
    """

    :param configs_path:
    :param config_list:
    :return:
    """
    setting_path = "./scrapy_weiboSpider/config_path_file.py"
    code_base = 'config_path = "{}/{}"'
    for config_filename in config_list:
        print("开始运行{}".format(config_filename))
        code = code_base.format(configs_path, config_filename)
        open(setting_path, "w", encoding="utf-8").write(code)
        os.system("scrapy crawl new_wb_spider")


def update_all_cookies(configs_path, new_cookies_dir):
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


if __name__ == '__main__':

    # 这里写新cookies
    new_cookeis = """
    
    
    
    """.strip()

    configs_path = "./configs"  # 这个是配置文件夹路径
    update_all_cookies(configs_path, new_cookeis)
    print("cookies更新完成，摁Esc退出或随便摁啥开始爬")
    x = ord(msvcrt.getch())
    if x == 27:
        os._exit(0)

    # 要跑哪些配置文件
    config_list = ["cat.json",
                   "duckliu.json"
                   ]

    run_all(configs_path, config_list)
