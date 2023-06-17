import json

filename1 = "wb_result.json"
filename2 = "r_wb_result.json"
wbs = json.load(open(filename1, "r", encoding="utf-8"))
print(f"微博数量{len(wbs)}")
print("r评论采样：")
for wb in wbs[:20]:
    rcomms = wb["comments"]
    ccomm_num_list = []
    for rcomm in rcomms:
        ccomm_num_list.append(len(rcomm["child_comm"]))
    print(f"{wb['wb_url'].split('?')[0]} {wb['content'][:10]} \tr评论数 {len(rcomms)} 子评论数列表 {ccomm_num_list}")
