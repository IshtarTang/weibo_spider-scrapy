import json
import pandas

# 放到prefile下，生成csv
for perfix in ["weibo", "ccomm", "rcomm"]:
    file = open("{}.txt".format(perfix), "r", encoding="utf-8").read().strip()
    json_str = ("[" + (",\n".join(file.split("\n"))) + "]").strip()
    wbs = json.loads(json_str)
    df = pandas.DataFrame(wbs)
    df.to_csv("./{}.csv".format(perfix))
