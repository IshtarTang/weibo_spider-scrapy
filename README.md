容我在自己的项目前面写个求助

请问有没有人在 2022年11月14日之后使用过这个或其他备份微博的程序 对@不死人后院画符bot_ (数字id：7567516224) 进行过备份，这个账号里有一些评论内容对我来说很重要。

如果有人能给我这个账号的数据的话真的非常感谢，为表感激之情我可以为你写点代码，爬个网站（不保证能成总之我尽力）或者给现在这个程序加功能什么的（我很想说我给你打钱但是我真的穷，等我有钱一点我就把这里改成给你打钱）

好了下面是这个程序的说明文档





* [使 用](#使用)
  * [配置文件](#配置文件)
  * [启动](#启动)
* [结果文件](#结果文件)
* [联系我](#联系我)
* [其他](#其他)



### 使用

<br>

#### 配置文件

配置文件在configs下，`n1_userWb_config.json`是爬取用户微博的配置文件，改这个就行。
l开头的为旧版微博配置项，已废弃（除非你能搞到旧版cookies），不用动。


可以在config放多个配置文件，只要按格式写就行，在`scrapy_weiboSpider/config_path_file.py`中设置你要启用的配置文件路径（用之前最好检查下这个，因为我老是把自己用的文件名push上来）。

灰框内为不用动的，蓝框内为基础设置，每个配置文件都有，橙框内为每个模式的功能设置

![1653041132255](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1653041132255.png)

<br>



**不用动的部分**

`description`：用来看的

`id`：用来确认启用哪个模式

**基础配置**

`cookies_str`：登录状态信息，没有这个只能获取到一页内容，[cookies 获取](./笔记图/README/新版cookies获取.png)

`print_level`：设为1的话会多一些输出内容，属于无关紧要的配置，反正日志里该有的都有

<br>

**用户主页爬取配置**

功能是爬取一个用户发过的所有微博

`user_id`：[userid 获取](./笔记图/README/id获取.png)

`user_name`：你要爬取的用户的用户名。不写也行，因为这个项影响的是文件保存位置，具体看结果文件那里的说明。

`time_range`：只爬取某个时间段的微博，功能未完成。

`get_comm_num`：限制保存多少评论，功能未完成。



<br><br><br>

#### 启动



 **环境配置**

首先你电脑肯定得装了python

项目路径下` pip install -r requirements.txt `

程序用到了redis来做进度记录和过滤，下载地址 https://github.com/tporadowski/redis/releases ，我用的版本是3.0.504。

解压后戳`redis-server.exe`，弹出右边的窗口就是启动成功了。

![1628613064721](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1628613064721.png)

<br>



**启动程序**

先按前面说的修改配置文件

改好后 项目路径下敲  `scrapy crawl new_wb_spider`

它就跑起来了，把它扔那该干啥干啥，别断网就行，啥时候想起来就看看它跑完没。

<br>

<br>







### 结果文件

结果文件在./file下的对应文件夹里

爬取用户主页的文件标识由`user_id` `user_name`  `time_range`决定，

只设置了`user_id`时，文件标识为user_id，

设置了`time_range`时，时间范围添加在user_id后（x是不设结束时间）

设置了`user_name`时，用户名添加在user_id前

`time_range`和 `user_name`都设置了，则两个都有

![1628655283246](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1628655283246.png)



结果文件夹的内容：

![1672024192551](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/1672024192551.png)

假如你爬了A的微博主页，其中wb_result.json中为A发过的所有微博，r_wb_result.json中为A所有转发微博的源微博。

[结果文件示例](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/保存文件示例.png) 

[结果文件中各字段的含义](%E7%AC%94%E8%AE%B0%E5%9B%BE/README/%E4%BF%9D%E5%AD%98%E6%96%87%E4%BB%B6%E5%AD%97%E6%AE%B5-1628644419723.png)

prefile中为过程文件。weibo是微博信息，rcomm是根评论信息，ccomm是子评论信息，程序结束时会整合到两个result文件中，运行结束后可以选择是否删除。



### 联系我

有问题的话我的邮箱是 ishtartang@163.com，如果是程序出问题最好把日志一块发给我，日志在项目路径下的log文件夹，格式是 日期_序号.log，发最新的一份就行
如果要讨论，微信号`Ishtar_Tang`，备注从微博爬虫来的。





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

