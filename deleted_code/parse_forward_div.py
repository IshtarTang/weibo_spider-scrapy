from lxml.html import etree
import time
import re

# 在第一次写的时候发现有种微博在转发微博里看得见，但是源微博的链接打不开，用其他浏览器试过并不是缓存，所以写了这个方法
# 把框架改为scrapy时找不到测试用例，所以暂时把这个方法删掉，等找到测试用例再加回来
def n_parse_weibo_from_forward_div(self, forward_div, t_bid):
    remark = ""
    remark += "该条微博信息由转发页解析出来，原微博链无法加载"
    parse = forward_div

    count = 0
    # 微博链接
    try:
        weibo_url = "https://weibo.com" + parse.xpath("//div[contains(@class,'WB_from')]/a/@href")[0]
    except:
        print("调用parse_weibo_from_div的参数有误，返回空weibo对象")
        time.sleep(3)
        # return weiboItem()
        return

    if self.config["print_level"]:
        print("开始解析链接 {}".format(weibo_url))

    # 用户id和bid
    bid_ele = parse.xpath(".//a[@node-type='feed_list_item_date']/@href")
    userid_and_bid_re = re.search("/(\d+)/(\w+)", bid_ele[0])
    user_id = userid_and_bid_re.group(1)
    bid = userid_and_bid_re.group(2)
    # 用户名
    user_name = parse.xpath(".//div/a[@class='W_fb S_txt1']/text()")[0]

    # 正文
    content_ele = parse.xpath(
        ".//div[@node-type='feed_list_forwardContent']//div[contains(@class,'WB_text')]//text()")
    content_ele[0] = content_ele[0].strip()
    content = "\n".join(content_ele).replace("\u200b", "").replace("//\n@", "//@").replace("\n:", ":").replace(
        "\xa0", "").replace("\xa1", "")
    # 有链接时会多出换行，可以在xpath处理但是太麻烦，所以直接replace
    content = content.replace("\nO\n网页链接", " O 网页链接")

    # 链接
    parse_links = parse.xpath(".//div[@node-type='feed_list_content']//a[@href and @rel]/@href")
    real_links = []
    for parse_link in parse_links:
        # try是有时候会有外网链接，请求失败
        try:
            link_response = self.session.get(parse_link)
            response_url = link_response.url

            if response_url != parse_link:
                # 直接将请求到的url放入列表
                real_links.append(response_url)
            else:
                # 需要从页面中解析出真正的url
                real_link = etree.HTML(link_response.text).xpath(".//div[contains(@class,'desc')]/text()")[
                    0].strip()
                real_links.append(real_link)

        except:
            real_links.append(parse_link)

    # 发表时间
    public_time = str(parse.xpath(".//div[contains(@class,'WB_from')]/a/@title")[0])
    # 发表时间戳
    public_timestamp = int(parse.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])

    # 图片链接
    img_list = []

    item_eles = parse.xpath(".//div[contains(@class,'WB_media_wrap clearfix')]//div[contains(@class,'media_box')]")
    # 存在item_ele
    if item_eles:
        item_ele = item_eles[0]
        img_info_list = item_ele.xpath(".//li[contains(@class,'WB_pic')]/@suda-uatrack")
        # 存在图片ele
        if img_info_list:
            img_list = [self.n_get_img_list(img_info) for img_info in img_info_list]
        else:
            img_list = []

    # 视频
    video_url = ""
    video_url_info = parse.xpath(".//li[contains(@class,'WB_video')]/@suda-uatrack")
    # 只保留原创视频链接
    if video_url_info:
        video_url_base = "https://weibo.com/tv/show/{}:{}"
        video_search = re.search(r":(\d+)%3A(\w+):", video_url_info[0])
        video_url = video_url_base.format(video_search.group(1), video_search.group(2))

    # 微博来源
    weibo_from_ele = parse.xpath(".//div[contains(@class,'WB_from')]//a[@action-type]/text()")
    if weibo_from_ele:
        weibo_from = weibo_from_ele[0]
    else:
        weibo_from = "未显示来源"

    # 文章 链接和内容
    article_url = ""
    article_content = ""
    article_url_ele = parse.xpath(".//div[contains(@class,'WB_feed_spec')]/@suda-uatrack")

    # 存在外链div
    if article_url_ele:
        article_url_base = "https://weibo.com/ttarticle/p/show?id={}"
        article_id_search = re.search(r"article:（\d+）:", article_url_ele[0])
        # 外链div为文章
        if article_id_search:
            article_url = article_url_base.format(article_id_search.group(1))
            article_parse = etree.HTML(self.session.get(article_url).text)
            article_content = "\n".join(article_parse.xpath(".//div[@node-type='contentBody']/p/text()"))
    # 赞  评论 转发
    forward_comment_like_ele = parse.xpath(".//span[@class='line S_line1']/a/span//em[last()]/text()")
    # 肯定有转发，不用判断
    forward_num_str = forward_comment_like_ele[0]
    try:
        forward_num = int(forward_num_str)
    except:
        if "万" in forward_num_str:
            forward_num = int(forward_num_str.split("万")[0]) * 10000
            remark += "\t 转发数过大，获取到的字符串为：{}".format(forward_num_str)
        else:
            forward_num = -1
            remark += "\t 转发数异常，获取到的字符串为：{}".format(forward_num_str)

    comment_num_str = forward_comment_like_ele[1]
    if comment_num_str != "评论":
        try:
            comment_num = int(comment_num_str)
        except:
            if "万" in comment_num_str:
                comment_num = int(comment_num_str.split("万")[0]) * 10000
                remark += "\t 评论数过大，获取到的字符串为：{}".format(comment_num_str)
            else:
                comment_num = -1
                remark += "\t 评论数异常，获取到的字符串为：{}".format(comment_num_str)
    else:
        comment_num = 0
    like_num_str = forward_comment_like_ele[2]
    if like_num_str != "赞":
        try:
            like_num = int(like_num_str)
        except:
            if "万" in like_num_str:
                like_num = int(like_num_str.split("万")[0]) * 10000
                remark += "\t 点赞数过大，获取到的字符串为：{}".format(like_num_str)
            else:
                like_num = -1
                remark += "\t 点赞数异常，获取到的字符串为：{}".format(like_num_str)
    else:
        like_num = 0

    # 调这个方法的绝对是原创公开微博，且获取不到评论
    is_original = 1
    share_scope = "公开"
    r_href = ""
    r_weibo = {}

    # weiboItem1 = weiboItem()
    weiboItem1 = {}
    weiboItem1["bid"] = bid
    weiboItem1["t_bid"] = t_bid
    weiboItem1["wb_url"] = weibo_url
    weiboItem1["user_id"] = user_id
    weiboItem1["user_name"] = user_name
    weiboItem1["content"] = content
    weiboItem1["public_time"] = public_time
    weiboItem1["public_timestamp"] = public_timestamp
    weiboItem1["share_scope"] = share_scope
    weiboItem1["like_num"] = like_num
    weiboItem1["forward_num"] = forward_num
    weiboItem1["comment_num"] = comment_num
    weiboItem1["is_original"] = is_original
    weiboItem1["r_href"] = r_href
    weiboItem1["links"] = real_links
    weiboItem1["img_list"] = img_list
    weiboItem1["weibo_from"] = weibo_from
    weiboItem1["article_url"] = article_url
    weiboItem1["article_content"] = article_content
    weiboItem1["video_url"] = video_url
    weiboItem1["remark"] = remark
    weiboItem1["r_weibo"] = r_weibo

    yield weiboItem1
