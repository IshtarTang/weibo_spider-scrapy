from selenium import webdriver
from tool import cookiestodic

cookies_str = "SINAGLOBAL=9660189142619.871.1625547924755; UOR=,,login.sina.com.cn; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFlK8wHn55LiDCvTD8mF1.n5JpX5KzhUgL.Fo2NShnpe0Bce0z2dJLoIpXXeCH8SC-RxbHFSEH8SE-RBEHWBbH8SE-RBEHWBntt; SSOLoginState=1668297245; SCF=AgQL8ho8S9VCgxHBFSlHE6KWEaQJeYzc4ESBw87Pq7JKnPCYIQNfQb6txdI9pW_-uUMycGnxXrBDIvlMUFht1tw.; SUB=_2A25OdEI-DeRhGedJ71oQ8yrKyD6IHXVtADT2rDV8PUNbmtANLVH_kW9NUeseWgDghlD-SKXx5BVW5rkf_igDiSfR; ALF=1699833325; wvr=6; _s_tentry=weibo.com; Apache=4721973954849.736.1668302406073; ULV=1668302406099:492:3:2:4721973954849.736.1668302406073:1668286345308; webim_unReadCount=%7B%22time%22%3A1668322678923%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22chat_group_notice%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A2%7D"
cookies = cookiestodic(cookies_str)

url1 = "https://photo.weibo.com/7375225084/wbphotos/large/mid/4835117065571461/pid/00837GXily1h81np58qzfj30u0140jy6"
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome("chromedriver.exe", options=options)
driver.get(url1)

driver.delete_all_cookies()
for key, value in cookies.items():
    driver.add_cookie({"name": key, "value": value})
driver.refresh()
driver.get(
    "https://photo.weibo.com/7375225084/wbphotos/large/mid/4835117065571461/pid/00837GXily1h81np58qzfj30u0140jy6")
html = driver.execute_script("return document.documentElement.outerHTML")
open("test.html", "w", encoding="utf-8").write(html)
