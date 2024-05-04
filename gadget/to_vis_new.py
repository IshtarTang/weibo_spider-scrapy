import json
import os

# ###################
#
#   放到wb_result.json同一路径，把数据处理成可视化程序用的数据
#
# ##################

filename = "wb_result.json"
vis_filename = "vis_" + filename
file = json.load(open(filename, "r", encoding="utf-8"))
n_wb_list = []

for wb in file[::-1]:
    wb["content"] = wb["content"].strip().replace(" ​​​", "")
    del wb["wb_url"]
    del wb["user_id"]
    del wb["user_name"]
    del wb["public_timestamp"]
    del wb["like_num"]
    del wb["forward_num"]
    del wb["weibo_from"]
    img_num = 0
    img_list = []
    index = 1
    bid = wb["bid"]
    for img in wb["img_list"]:
        img_filename = bid + "_" + str(index) + ".jpg"
        index += 1
        img_list.append(img_filename)
        img_num += 1

    wb["img_num"] = img_num

    wb["img_list"] = img_list
    comms_list = []
    comm_count = 0
    for rcomm in wb["comments"]:
        comm_count += 1
        a_comm_list = []
        rcomm_str = rcomm["user_name"] + ": " + rcomm["content"]
        if rcomm["img_url"]:
            rcomm_str += f"[{rcomm['img_url']}]"
        if rcomm["link"]:
            rcomm_str += str(rcomm["link"])
        a_comm_list.append(rcomm_str)
        for ccomm in rcomm["child_comm"]:
            comm_count += 1
            ccomm_str = ccomm["user_name"] + ": " + ccomm["content"]
            if ccomm["img_url"]:
                ccomm_str += f"[{ccomm['img_url']}]"

            if ccomm["link"]:
                ccomm_str += str(ccomm["link"])
            a_comm_list.append(ccomm_str)
        comms_list.append("\n    ".join(a_comm_list))
    wb["vis_comms"] = comms_list
    wb["comm_count"] = comm_count
    del wb["comments"]
    n_wb_list.append(wb)

json.dump(n_wb_list, open(vis_filename, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
