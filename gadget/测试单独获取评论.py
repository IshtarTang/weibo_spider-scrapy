import requests
from gadget import comm_tool

mid = 4872765406975235
user_id = 3514695127
# mid = 4835319768424065
# user_id = 7567516224
comm_url_base = "https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&" \
                "id={}&is_show_bulletin=2&is_mix=0&count=10&uid={}"
comm_url = comm_url_base.format(mid, user_id)
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"}
cookies_str = "SINAGLOBAL=5099002790593.161.1676951216879; UOR=,,login.sina.com.cn; ULV=1679932099939:5:3:1:5647940532643.714.1679932099936:1679049753459; XSRF-TOKEN=FqpUjKsCru_pO4jR2VT1XuvA; SCF=AgQL8ho8S9VCgxHBFSlHE6KWEaQJeYzc4ESBw87Pq7JKMndLcSPpK2ofbpFg7sOR26blv2FgZ0vYuohED-HpDlU.; SUB=_2A25JLfXxDeRhGeBL4lMX8ybFyTSIHXVqW2A5rDV8PUNbmtAGLXamkW9NRte-qS3_-IHmOpdracKMXiEd4onw2hRI; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFgpqB02S8a2UJmEK1y8vEg5JpX5KzhUgL.Foqf1K2ce0n4eon2dJLoI7fJUPxfMJHkqcvEMGSL; ALF=1711978783; SSOLoginState=1680442785; WBPSESS=70AlSVZcFbZ5lizvBDd0tDFKRXbmy4RfksqaNBHBn_E9dIVJDMftn1umvYAQyR6sF6pn4Tm5TJ-Dua93XamQPmu9k11Q6DvxmY9pEc3hFQOMxr2mcC3ULR5D4hAxxIG7fXXtHHKuxbp1Nvprn5UBng=="
cookies = comm_tool.cookiestoDic(cookies_str)

response = requests.get(comm_url)
content = response.text
print(content)
open("test.html", "w", encoding="utf-8").write(content)
print(response.status_code)
