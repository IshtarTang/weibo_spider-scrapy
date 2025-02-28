import os
from spider_tool import merge_wb


def merge_result_file(dirs:list, result_path):
    """
    把同一个用户 两次不同key的结果文件合并成一个
    :param dirs: 结果文件路径列表，到 /Key 就行，不用到 /prefile
    :param result_path: 合并之后放哪
    :return:
    """
    sep = os.path.sep
    result_prefile_path = f"{result_path}{sep}prefile"
    if not os.path.exists(result_path):
        os.makedirs(result_prefile_path)
    all_ccomm = []
    all_rcomm = []
    all_weibo = []

    pre_files = {"ccomm.txt": all_ccomm,
                 "rcomm.txt": all_rcomm,
                 "weibo.txt": all_weibo}

    for key, value in pre_files.items():
        for dir in dirs:
            with open(f"{dir}{sep}{key}", "r", encoding="utf-8") as op:
                value += op.read().strip().split("\n")
        with open(f"{result_prefile_path}{sep}{key}", "w", encoding="utf-8") as op:
            op.write("\n".join(value))


if __name__ == '__main__':
    # 把同一个用户 两次不同key的结果文件合并成一个
    dirs = ["path1", "path2", "path3"]  # 文件路径，到 /Key 就行，不用到 /prefile
    result_path = "result_path"  # 合并之后放哪
    merge_result_file(dirs, result_path)
    mw = merge_wb.MergeWbFile(result_path, "userid", 1)
    mw.run()
