# # -*- coding: utf-8 -*-
# import json
# from scrapy_weiboSpider.utils.log_print_utils import log_and_print
# from scrapy_weiboSpider import  parsers, fetcher
#
#
# class CallbackFuns:
#     """
#     一些经努力解耦合后的callback方法，能很方便的拷到spider里使
#     """
#
#     def parse_comms(self, response):
#         """
#         root评论和child评论都走这个方法解析&翻页，用meta["comm_type"]区别
#         meta中必须有以下值
#         上级id superior_id、评论类型 comm_type 、用户id user_id、
#         评论计数 comm_fetched、根评论目标数 rcomm_target，子评论目标数（这部分之后要改成可选项）
#         """
#         content = response.text
#         j_data = json.loads(content)
#         meta = response.meta
#
#         superior_id = meta["superior_id"]  # 上级的id
#         blog_user_id = meta["blog_user_id"]  # 用户id
#         comm_type = meta["comm_type"]  # 评论类型
#         ccomm_target = meta["ccomm_target"]
#         rcomm_target = meta["rcomm_target"]
#
#         comms = j_data["data"]  # 获取到的评论数据，是个list，一条一个评论
#         # 评论一条一条塞到解析方法里
#         for comm in comms:
#             # 提取item
#             comm_item = parsers.extract_comm_item(comm, superior_id, comm_type)
#             yield comm_item
#             meta["comm_fetched"] += 1  # 确认送去解析再 +1
#
#             comment_id = comm_item["comment_id"]
#             # 是否有子评论，有的且需要的话送去请求
#             if comm.get("comments", []) and ccomm_target:
#                 yield fetcher.build_firse_ccomment_request(
#                     comment_id, blog_user_id, rcomm_target, ccomm_target,
#                     self.parse_comms, self.comm_headers, self.cookies)
#
#         message = "获取到{} comm {} 条，上级为 {}，重试{}次". \
#             format(comm_type, len(comms), superior_id, meta.get("failure_with_max_id", 0))
#         log_and_print(message, "debug")
#
#         # 下一页评论
#         comment_turning_gen = fetcher.build_comment_turning_request(
#             response, self.cookies, self.comm_headers, self.parse_comms)
#
#         status, message = next(comment_turning_gen)
#
#         if status == "ok":  # 有且要继续翻页，会再反一个request回来
#             comment_turning_request = next(comment_turning_gen)
#             yield comment_turning_request
#         elif status == "wb limit":  # 微博限制评论显示
#             message = f"{superior_id} 下 {comm_type} 状态： {message}，结束获取该条微博评论"
#             log_and_print(message, "info")
#         elif status == "no max_id":  # 没有下一页
#             message = f"{blog_user_id}/{superior_id} 无更多评论，获取结束"
#             log_and_print(message, "info")
#         elif status == "comm_limit":  # 已获取设定的条数
#             message = f"{comm_type} {blog_user_id}/{superior_id} 已经获取足够评论条数{message} "
#             log_and_print(message, "info")
#             message = ""
#
#     def get_long_text(self, response):
#         """
#
#         :param response:
#         :return:
#         """
#         content = response.text
#         j_data = json.loads(content)
#         meta = response.meta
#         meta["count"] += 1
#         wb_item = meta["wb_item"]
#
#         if j_data["ok"] and j_data["data"]:
#             # 确实是长微博
#             if j_data["data"]:
#                 content = j_data["data"]["longTextContent"]
#                 wb_item["content"] = content
#             yield wb_item
#             message = "{} 解析完毕:{}".format(wb_item["wb_url"], content[:10].replace("\n", "\t"))
#             log_and_print(message, "DEBUG")
#
#         elif j_data["ok"]:
#             # 判断是否长微博是用长度判断的，可能出现误判，获取长文本未返回数据
#             # 这种情况直接用之前的短文本就行
#             yield wb_item
#         else:
#             log_and_print("{} 长文获取失败", "warn")
#             yield wb_item
