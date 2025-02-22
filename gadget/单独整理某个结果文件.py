from spider_tool import merge_wb

m = merge_wb.MergeWbFile("configs_auto/", "3514695127", 1)
m.drop_duplication()