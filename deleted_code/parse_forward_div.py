from lxml.html import etree
import time
import re

# �ڵ�һ��д��ʱ��������΢����ת��΢���￴�ü�������Դ΢�������Ӵ򲻿���������������Թ������ǻ��棬����д���������
# �ѿ�ܸ�Ϊscrapyʱ�Ҳ�������������������ʱ���������ɾ�������ҵ����������ټӻ���
def n_parse_weibo_from_forward_div(self, forward_div, t_bid):
    remark = ""
    remark += "����΢����Ϣ��ת��ҳ����������ԭ΢�����޷�����"
    parse = forward_div

    count = 0
    # ΢������
    try:
        weibo_url = "https://weibo.com" + parse.xpath("//div[contains(@class,'WB_from')]/a/@href")[0]
    except:
        print("����parse_weibo_from_div�Ĳ������󣬷��ؿ�weibo����")
        time.sleep(3)
        # return weiboItem()
        return

    if self.config["print_level"]:
        print("��ʼ�������� {}".format(weibo_url))

    # �û�id��bid
    bid_ele = parse.xpath(".//a[@node-type='feed_list_item_date']/@href")
    userid_and_bid_re = re.search("/(\d+)/(\w+)", bid_ele[0])
    user_id = userid_and_bid_re.group(1)
    bid = userid_and_bid_re.group(2)
    # �û���
    user_name = parse.xpath(".//div/a[@class='W_fb S_txt1']/text()")[0]

    # ����
    content_ele = parse.xpath(
        ".//div[@node-type='feed_list_forwardContent']//div[contains(@class,'WB_text')]//text()")
    content_ele[0] = content_ele[0].strip()
    content = "\n".join(content_ele).replace("\u200b", "").replace("//\n@", "//@").replace("\n:", ":").replace(
        "\xa0", "").replace("\xa1", "")
    # ������ʱ�������У�������xpath������̫�鷳������ֱ��replace
    content = content.replace("\nO\n��ҳ����", " O ��ҳ����")

    # ����
    parse_links = parse.xpath(".//div[@node-type='feed_list_content']//a[@href and @rel]/@href")
    real_links = []
    for parse_link in parse_links:
        # try����ʱ������������ӣ�����ʧ��
        try:
            link_response = self.session.get(parse_link)
            response_url = link_response.url

            if response_url != parse_link:
                # ֱ�ӽ����󵽵�url�����б�
                real_links.append(response_url)
            else:
                # ��Ҫ��ҳ���н�����������url
                real_link = etree.HTML(link_response.text).xpath(".//div[contains(@class,'desc')]/text()")[
                    0].strip()
                real_links.append(real_link)

        except:
            real_links.append(parse_link)

    # ����ʱ��
    public_time = str(parse.xpath(".//div[contains(@class,'WB_from')]/a/@title")[0])
    # ����ʱ���
    public_timestamp = int(parse.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])

    # ͼƬ����
    img_list = []

    item_eles = parse.xpath(".//div[contains(@class,'WB_media_wrap clearfix')]//div[contains(@class,'media_box')]")
    # ����item_ele
    if item_eles:
        item_ele = item_eles[0]
        img_info_list = item_ele.xpath(".//li[contains(@class,'WB_pic')]/@suda-uatrack")
        # ����ͼƬele
        if img_info_list:
            img_list = [self.n_get_img_list(img_info) for img_info in img_info_list]
        else:
            img_list = []

    # ��Ƶ
    video_url = ""
    video_url_info = parse.xpath(".//li[contains(@class,'WB_video')]/@suda-uatrack")
    # ֻ����ԭ����Ƶ����
    if video_url_info:
        video_url_base = "https://weibo.com/tv/show/{}:{}"
        video_search = re.search(r":(\d+)%3A(\w+):", video_url_info[0])
        video_url = video_url_base.format(video_search.group(1), video_search.group(2))

    # ΢����Դ
    weibo_from_ele = parse.xpath(".//div[contains(@class,'WB_from')]//a[@action-type]/text()")
    if weibo_from_ele:
        weibo_from = weibo_from_ele[0]
    else:
        weibo_from = "δ��ʾ��Դ"

    # ���� ���Ӻ�����
    article_url = ""
    article_content = ""
    article_url_ele = parse.xpath(".//div[contains(@class,'WB_feed_spec')]/@suda-uatrack")

    # ��������div
    if article_url_ele:
        article_url_base = "https://weibo.com/ttarticle/p/show?id={}"
        article_id_search = re.search(r"article:��\d+��:", article_url_ele[0])
        # ����divΪ����
        if article_id_search:
            article_url = article_url_base.format(article_id_search.group(1))
            article_parse = etree.HTML(self.session.get(article_url).text)
            article_content = "\n".join(article_parse.xpath(".//div[@node-type='contentBody']/p/text()"))
    # ��  ���� ת��
    forward_comment_like_ele = parse.xpath(".//span[@class='line S_line1']/a/span//em[last()]/text()")
    # �϶���ת���������ж�
    forward_num_str = forward_comment_like_ele[0]
    try:
        forward_num = int(forward_num_str)
    except:
        if "��" in forward_num_str:
            forward_num = int(forward_num_str.split("��")[0]) * 10000
            remark += "\t ת�������󣬻�ȡ�����ַ���Ϊ��{}".format(forward_num_str)
        else:
            forward_num = -1
            remark += "\t ת�����쳣����ȡ�����ַ���Ϊ��{}".format(forward_num_str)

    comment_num_str = forward_comment_like_ele[1]
    if comment_num_str != "����":
        try:
            comment_num = int(comment_num_str)
        except:
            if "��" in comment_num_str:
                comment_num = int(comment_num_str.split("��")[0]) * 10000
                remark += "\t ���������󣬻�ȡ�����ַ���Ϊ��{}".format(comment_num_str)
            else:
                comment_num = -1
                remark += "\t �������쳣����ȡ�����ַ���Ϊ��{}".format(comment_num_str)
    else:
        comment_num = 0
    like_num_str = forward_comment_like_ele[2]
    if like_num_str != "��":
        try:
            like_num = int(like_num_str)
        except:
            if "��" in like_num_str:
                like_num = int(like_num_str.split("��")[0]) * 10000
                remark += "\t ���������󣬻�ȡ�����ַ���Ϊ��{}".format(like_num_str)
            else:
                like_num = -1
                remark += "\t �������쳣����ȡ�����ַ���Ϊ��{}".format(like_num_str)
    else:
        like_num = 0

    # ����������ľ�����ԭ������΢�����һ�ȡ��������
    is_original = 1
    share_scope = "����"
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
