import json


def to_txt(fp, get_comm):
    for wb in wbs:
        pb_time = wb["public_time"]
        content = wb["content"]
        user_name = wb["user_name"]
        like_num = wb["like_num"]
        forward_num = wb["forward_num"]
        comment_num = wb["comment_num"]
        is_original = wb["is_original"]
        wb_url = wb["wb_url"]
        txt_content = f"{user_name}\n{pb_time}  原博链接 {wb_url}\n{content}"
        if not is_original:
            r_weibo = wb["r_weibo"]
            # r_weibo_content = "\n[转发内容]\n" + r_weibo['user_name'] + "：" + r_weibo['content']
            r_weibo_content = f"\n[转发内容]\n{r_weibo['user_name']}：{r_weibo['content']}"
            txt_content += r_weibo_content
        hot_info = "\n" + "--" * 20 + f"\n点赞数{like_num}  评论数{comment_num} 转发数{forward_num}"
        txt_content += hot_info
        if get_comm:
            if comment_num > 0:
                comm_txt = "\n评论详情\n"
                comms = wb["comments"]
                for comm in comms:
                    comm_txt += f"\t[{comm['date']}]{comm['user_name']}：{comm['content']}"
                    if comm["link"]:
                        comm_txt += f"（携带外链{comm['link']}）"
                    comm_txt += "\n"
            else:
                comm_txt = "无有效评论"
            txt_content += comm_txt
        txt_tail = "\n" * 4 + "==" * 20 + "\n" * 2
        txt_content += txt_tail
        fp.write(txt_content)


wbs = json.load(open("wb_result.json", "r", encoding="utf-8"))
txt_fp = open("resutl.txt", "w", encoding="utf-8")
to_txt(txt_fp, 1)
txt_fp.close()
