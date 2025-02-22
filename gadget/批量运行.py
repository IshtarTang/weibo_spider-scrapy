import os
import json
from configs import update_all_cookies
from configs_auto.a_all_config import config_list


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


def update_all_cookies_(configs_path, new_cookies_dir):
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


def get_configs(dir):
    files = os.listdir(dir)
    files = filter(lambda x: ".json" in x, files)
    return list(files)


if __name__ == '__main__':
    """
    批量备份一堆微博主页
    """

    # 这里写新cookies

    new_cookeis = """
UOR=,,login.sina.com.cn; SCF=AgQL8ho8S9VCgxHBFSlHE6KWEaQJeYzc4ESBw87Pq7JK9ppaV_6uDX6qaqUN8zGwiTOqVuEm42uDYkfDyjDPjt0.; SINAGLOBAL=1759562917537.7358.1711554178012; ALF=1718024741; SUB=_2A25LOx11DeRhGeBL4lMX8ybFyTSIHXVoORC9rDV8PUJbkNANLWPNkW1NRte-qWlZ3FUPDULTD6SirfU62BYKdFcu; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFgpqB02S8a2UJmEK1y8vEg5JpX5KMhUgL.Foqf1K2ce0n4eon2dJLoI7fJUPxfMJHkqcvEMGSL; ULV=1715526832956:121:5:1:2522996679599.678.1715526832897:1715366825684; XSRF-TOKEN=f9xPbauY6OzerZkHaK68yKJJ; WBPSESS=70AlSVZcFbZ5lizvBDd0tDFKRXbmy4RfksqaNBHBn_E9dIVJDMftn1umvYAQyR6seXhEgF46R2HWOFMYmK5fxKq_e0VUIEofaivEy3IqrsYAfDjVBUtEKfWaCyxWIW53lNeWPAiwfo0tEwoIF8NbFg==

    """.strip()

    configs_path = "./configs_auto"  # 这个是配置文件夹路径
    update_all_cookies.update(configs_path, new_cookeis)
    x = input("cookies更新完成，输入ok开爬\n")
    # if x != "ok" and x != "":
    #     exit()

    # 要跑哪些配置文件
    run_all(configs_path, config_list)
