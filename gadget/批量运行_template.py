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
        order = f"scrapy crawl new_wb_spider -s CONFIG_PATH={config_filename}"
        os.system(order)
        print(order)


if __name__ == '__main__':
    """
    把这个复制到项目路径下运行
    依次运行configs_path下所有配置文件

    记得走命令行启动，不然按不了Ctrl+C
    """
    configs_path = "auto_configs"  # 放配置文件的文件夹
    changes = {

        "cookies_str": """
        
        """.strip()  # 在这里放新cookies
    }
    # 把cookies更新到所有的配置文件里，并且拿到所有配配置文件的路径
    config_paths = 批量处理配置文件.nodify_configs(changes, configs_path, 1)
    # print(config_paths)
    run_all(config_paths)
