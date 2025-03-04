

## 配置文件

默认使用配置文件`configs/dufault_config.json`

 ![1741091333272](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1741091333272.png)



#### 不用动的部分

`description`：用来看的

`id`：用来确认启用哪个模式，虽然目前只写了一个模式



### 基础配置

`cookies_str`：登录状态信息，没有这个只能获取到一页内容，[cookies 获取](./笔记图/README/新版cookies获取.png)

`user_id`：你要存的账号的userid [userid 获取](./笔记图/README/id获取.png)



### 功能配置项

#### get_rwb_detail

是否获取被转发微博的详细信息，1获取，0不获取



#### time_limit

时间限制功能，有三种模式

- 手动模式，获取现在到设定时间内的微博

  - 填  yyyy-MM-dd HH:mm 格式的字符串，例："2024-01-01 00:00"
  - 填 int毫秒级时间戳，例：1710655039000

- 自动模式1

  填入"auto"，如果结果文件路径有内容，程序会提取结果文件`wb_result.json`里最新一条微博的时间，只获取现在到该时间的微博。

- 自动模式2

  填入"auto2"，如果结果文件路径有内容，保存所有不在结果文件里的微博

手动模式和auto都会限制翻页，即：如果第5页的所有微博都早于设定的时间，那就不会继续翻第6页。auto2与页数无关，会把主页全翻一遍

如果用自动模式，那程序结束的时候问要不要清预存文件时一定要选no，因为结果文件是用预存文件处理出来的，预存清掉了下次运行产生的结果文件就不会有上次保存的内容。

#### get_comm_num

保存多少评论，设为 -1 就是保存所有评论

​		`wb_rcomm`：爬取每条微博下的多少根评论

​		`wb_ccomm`：爬取每条根评论下的多少子评论

​		`rwb_rcomm`：爬取被转发微博下的多少根评论

​		`rwb_ccomm`：爬取被转发微博每条根评论下的多少子评论



一个请求最多返回20条评论，根评论和子评论都是，爬评论多的账号会花很久



##### 结果文件路径和其它配置

`dir_path`: 结果文件的文件夹放哪

`user_name`：会加在结果文件夹名字上user_name，方便认



`print_level`：设为1的话会多一些输出内容，在各种修之后好像已经没用了

`ensure_ask` : 设成 0 的话会取消开始和结束时要按一下键盘，结束默认保存预存文件。方便我自动化小工具的配置。



#### 启动

**redis**

程序用到了redis来做进度记录，没装的话自己去这下 https://github.com/tporadowski/redis/releases ，我用的版本是3.0.504，开程序前把`redis-server.exe`启动

**启动程序**

启动指令

```
scrapy crawl new_wb_spider
```

可以指定要使用的配置文件

```
scrapy crawl new_wb_spider -s CONFIG_PATH=config文件路径 
```



### 结果文件

结果文件默认在 `程序运行路径/file`

爬取用户主页的文件标识由`user_id` `user_name` 决定，

只设置了`user_id`时，文件标识为user_id，

设置了`user_name`时，用户名添加在user_id前

 ![1628655283246](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1628655283246.png)



结果文件夹的内容：

![1672024192551](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1672024192551.png)

你爬了A的微博主页，wb_result.json中为A发过的所有微博，r_wb_result.json中为所有被A转发的微博，如果把`get_rwb_detail`设为0，则不会有r_wb_result.json，而是sr_wb_result.json。

[结果文件中各字段的含义](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/%E4%BF%9D%E5%AD%98%E6%96%87%E4%BB%B6%E5%AD%97%E6%AE%B5-1628644419723.png)

prefile中为预存文件，weibo是微博信息，rcomm是根评论信息，ccomm是子评论信息，程序结束时会整合到两个result文件中，运行结束会问你删不删。





### 小工具

gadget里是一些方便我自己用的小工具，怎么用都写在各自的注释里，有些注释可能写得只有我自己看得懂，看得懂就用，看不懂算了。



### 联系我

一般问题提issue就行，如果有什么你觉得要加微信的事的话我的微信号是`Ishtar_Tang`，备注从微博爬虫来的。





### 其他

程序并爬取用户主页时，首先请求这个页面 [李镜合首页](https://weibo.com/u/6227479352?is_all=1) ，一次请求可以获取到20条微博，这个页面足够获取到大多数微博的完整信息，可以直接进行解析。但超过140字的微博会被折叠，这种时候才会请求微博详情页，比如 [李镜合的微博](https://weibo.com/6227479352/KrpUXclws)

<br>

不用再往下看了，这个上面有，直接在上面插表格感觉看着很不爽，所以上面插的图片链接，这是为了方便以后万一要修改留的表格备份。

文件中各字段含义

| 键               | 含义                                                  | 类型              |
| ---------------- | ----------------------------------------------------- | ----------------- |
| bid              | 微博bid，一条微博的唯一标识                           | str               |
| t_bid            | 哪条微博转发了当前微博，只有r_wb_result中的此项不为空 | str               |
| weibo_url        | 该条微博链接                                          | str               |
| user_id          | 用户id                                                | str               |
| user_name        | 用户名                                                | str               |
| content          | 微博正文                                              | str               |
| public_time      | 发表时间                                              | str               |
| public_timestamp | 发表时间戳                                            | int               |
| share_scope：    | 可见范围                                              | str               |
| like_num         | 点赞数                                                | int               |
| forward_num      | 转发数                                                | int               |
| comment_num      | 评论数                                                | int               |
| is_original      | 是否为原创，原创为1，转发为0，快转为-1                | int               |
| links            | 微博正文中包含的链接                                  | list，list中为str |
| img_list         | 图片链接列表                                          | list，list中为str |
| video_url        | 视频链接                                              | str               |
| weibo_from       | 微博来源                                              | str               |
| article_url      | 文章链接                                              | str               |
| article_content  | 文章内容                                              | str               |
| remark           | 备注                                                  | str               |
| r_href           | 如果是转发的微博，这里是源微博的url，否则空           | str               |
| r_weibo          | 如果是转发的微博，这里是源微博的简单信息，否则空      | str               |
| comments         | 评论信息列表                                          | dict              |



comments下各字段含义

| 键              | 含义                                                      | 类型 |
| --------------- | --------------------------------------------------------- | ---- |
| content         | 评论内容                                                  | str  |
| user_name       | 评论人的名字                                              | str  |
| user_url        | 评论人主页链接                                            | str  |
| comment_date    | 评论时间                                                  | str  |
| comment_type    | 直接回复微博的评论为root评论，评论下的回复为child评论     | str  |
| parent_comment  | child_comment是回复了哪条评论，root评论无parent_comment， | str  |
| like_num        | 点赞数                                                    | int  |
| comment_img_url | 评论中带的图片链接                                        | str  |
| link            | 评论中带的链接                                            | str  |
| chile_comm      | 子评论，即该条评论下的回复，子评论键值内容与父评论相同    |      |

