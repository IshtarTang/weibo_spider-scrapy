import json
import pandas as pd

wbs = json.load(open("wb_result.json", "r", encoding="utf-8"))
for wb in wbs:
    r_weibo = wb["r_weibo"]
    if r_weibo:
        r_weibo_txt = f"{r_weibo['user_name']}：{r_weibo['content']}"
        wb["r_weibo"] = r_weibo_txt
    else:
        wb["r_weibo"] = ""
    comms = wb["comments"]
    comms_txt = ""
    for comm in comms:
        comm_txt = f"[{comm['date']}]{comm['user_name']}：{comm['content']}\n"
        comms_txt += comm_txt
    wb["comments"] = comms_txt
    del wb["bid"]
    del wb["user_id"]
    del wb["public_timestamp"]
    del wb["share_scope"]
    del wb["weibo_from"]
    del wb["t_bid"]
    del wb["remark"]
    del wb["article_url"]
    del wb["article_content"]
df = pd.DataFrame(wbs)
df.to_excel("test.xlsx")
# json.dump(wbs, open("json_test.json", "w", encoding="utf-8"),ensure_ascii=False,indent=4)
