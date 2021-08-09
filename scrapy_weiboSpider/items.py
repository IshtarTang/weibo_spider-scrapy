# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class weiboItem(scrapy.Item):
    """
     bid: 微博bid
     t_bid：如果这是一条转发微博的源微博，此为转发微博的链接
     weibo_url: 微博链接
     user_id: 用户id
     user_name: 用户名
     content: 微博正文
     public_time: 发表时间
     public_timestamp: 发表时间戳
     share_scope: 可见范围
     like_num: 点赞数
     forward_num: 转发数
     comment_num: 评论数
     comment_list: 评论列表
     is_original: 是否为原创，原创为1，转发为0，快转为-1
     r_href: 原微博url
     links: 微博正文中包含的链接
     img_list: 图片链接列表
     video_url: 视频链接
     weibo_from: 微博来源
     article_url: 文章链接
     article_content: 文章内容
     remark: 备注
     r_weibo: 源微博
    """
    bid = scrapy.Field()
    t_bid = scrapy.Field()
    wb_url = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    content = scrapy.Field()
    public_time = scrapy.Field()
    public_timestamp = scrapy.Field()
    share_scope = scrapy.Field()
    like_num = scrapy.Field()
    forward_num = scrapy.Field()
    comment_num = scrapy.Field()
    is_original = scrapy.Field()


    r_href = scrapy.Field()
    links = scrapy.Field()
    img_list = scrapy.Field()
    video_url = scrapy.Field()
    weibo_from = scrapy.Field()
    article_url = scrapy.Field()
    article_content = scrapy.Field()
    remark = scrapy.Field()
    r_weibo = scrapy.Field()


class commentItem(scrapy.Item):
    # 寻找上级的标记
    comment_type = scrapy.Field()
    superior_id = scrapy.Field()
    # 字段部分
    comment_id = scrapy.Field()
    content = scrapy.Field()
    user_name = scrapy.Field()
    user_url = scrapy.Field()
    date = scrapy.Field()
    like_num = scrapy.Field()
    img_url = scrapy.Field()
    link = scrapy.Field()


class simpleExceptionLogItem(scrapy.Item):
    log = scrapy.Field()
