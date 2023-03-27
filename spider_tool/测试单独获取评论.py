import requests
from spider_tool import comm_tool

mid = 4872765406975235
user_id = 3514695127
# mid = 4835319768424065
# user_id = 7567516224
comm_url_base = "https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&" \
                "id={}&is_show_bulletin=2&is_mix=0&count=10&uid={}"
comm_url = comm_url_base.format(mid, user_id)
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"}
cookies_str = "SINAGLOBAL=5099002790593.161.1676951216879; UOR=,,login.sina.com.cn; XSRF-TOKEN=_lOGFaoxMns-gotjSjlrFSWr; SSOLoginState=1679507613; SCF=AgQL8ho8S9VCgxHBFSlHE6KWEaQJeYzc4ESBw87Pq7JKaJJdOg5OmcwlokOoM1QCyUETyEVFdGb35z6sLE8k_SE.; ALF=1711043611; SUB=_2AkMTfTWNf8NxqwJRmP4RzGPmboh_yAnEieKlIcRWJRMxHRl-yT9vqnM5tRB6OP0bYrcl-QfpiypnhDzU7Z54UWMcWvZJ; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9W5u.1BPITzPQXbCP_1vwqZD; login_sid_t=0ec01901d5c4f3c82a02083c2a9ac961; cross_origin_proto=SSL; _s_tentry=passport.weibo.com; Apache=5647940532643.714.1679932099936; ULV=1679932099939:5:3:1:5647940532643.714.1679932099936:1679049753459; WBPSESS=kErNolfXeoisUDB3d9TFHxnxvzvbn8q3aLpHCldp2U95AUtT3kyX6cmWukxURK6C1HNbfc77GqGGHPbEAGMSIKlNFKau2q2-AZphNXZ4G2L9hi4uSIgQDr482W3oR-BWO_9YMrNRKizEKdMfINmci_gVDk_RWpqbO0sOl4nctxI="
cookies = comm_tool.cookiestoDic(cookies_str)

response = requests.get(comm_url)
content = response.text
print(content)
open("test.html", "w", encoding="utf-8").write(content)
print(response.status_code)
