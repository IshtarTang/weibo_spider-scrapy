import os
import 批量处理配置文件


def run_all(config_list):
    """
    :param configs_path:
    :param config_list:
    :return:
    """
    setting_path = f"scrapy_weiboSpider{os.sep}config_path_file.py"
    for config_filename in config_list:
        print("开始运行{}".format(config_filename))
        code = f'config_path = r"{config_filename}"'
        open(setting_path, "w", encoding="utf-8").write(code)
        os.system("scrapy crawl new_wb_spider")


if __name__ == '__main__':
    """
    把这个复制到项目路径下运行
    批量备份一堆微博主页
    """
    configs_path = "auto_configs"  # 放配置文件的文件夹
    changes = {
        "cookies_str": """

SINAGLOBAL=1759562917537.7358.1711554178012; UOR=,,cn.bing.com; SCF=Am8qkLrUcYwfwLiBKAPdVzBeNkWpM2AARkNAJQyCP_PQoqE912eHv05Jz_F5V_wOv_oe3zTq0WC9E0tb817TXj0.; ALF=1742670415; SUB=_2A25Ksw0fDeRhGeBL4lMX8ybFyTSIHXVpsQDXrDV8PUJbkNANLRmnkW1NRte-qSVJLyGadnrW9CIrmgWiSgt7kAuI; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFgpqB02S8a2UJmEK1y8vEg5JpX5K-hUgL.Foqf1K2ce0n4eon2dJLoI7fJUPxfMJHkqcvEMGSL; XSRF-TOKEN=akoQ7fTymv51oy6CozNqao9t; _s_tentry=weibo.com; Apache=2635505304152.6787.1740317789036; ULV=1740317789082:183:5:2:2635505304152.6787.1740317789036:1740267970870; WBPSESS=70AlSVZcFbZ5lizvBDd0tDFKRXbmy4RfksqaNBHBn_E9dIVJDMftn1umvYAQyR6sl_tYfYuP9cfcIn_CnYbIzUzVC7Wd0AwJ2oIhgtmcryJIBdzmHhVI6qEArQ-qrMqvOo00kZ2GNqQtqDeD33brOQ==

        """.strip()
    }
    config_paths = 批量处理配置文件.nodify_configs(changes, configs_path, 1)
    # print(config_paths)
    run_all(config_paths)
