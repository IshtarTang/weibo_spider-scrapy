import json

# 寻找评论用户为鹿友
path = "file/[cat41]1748134632"
filename = "wb_result.json"
file = open(path + "/" + filename, "r", encoding="utf-8").read()
wbs = json.loads(file)
result_wbs = []
for wb in wbs:
    comments = wb["comments"]
    for comment in comments:
        if "鹿友" in comment["user_name"]:
            result_wbs.append(wb)
            break
with open(path + "/f_result.json", "w", encoding="utf-8") as op:
    op.write(json.dumps(result_wbs, indent=4, ensure_ascii=False))
print(len(result_wbs))
for wb in result_wbs:
    print(wb["wb_url"])
