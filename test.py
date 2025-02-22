import requests

cookies = {
    'SINAGLOBAL': '1759562917537.7358.1711554178012',
    'UOR': ',,cn.bing.com',
    'XSRF-TOKEN': 'sk5nYbHpPyIRnd92aA6SJlKs',
    '_s_tentry': 'weibo.com',
    'Apache': '699677657009.7229.1739280829144',
    'ULV': '1739280829226:180:2:1:699677657009.7229.1739280829144:1738948536603',
    'ALF': '1742011889',
    'SUB': '_2A25KqQChDeRhGeBL4lMX8ybFyTSIHXVpxxxprDV8PUJbkNANLU3dkW1NRte-qV4ItWIjDJCe8NByKpm17Zkp9Npa',
    'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9WFgpqB02S8a2UJmEK1y8vEg5JpX5KMhUgL.Foqf1K2ce0n4eon2dJLoI7fJUPxfMJHkqcvEMGSL',
    'WBPSESS': '70AlSVZcFbZ5lizvBDd0tDFKRXbmy4RfksqaNBHBn_E9dIVJDMftn1umvYAQyR6seXhEgF46R2HWOFMYmK5fxCHRrQnIs-VN36L9gDsxevtYGIaOQ5lBH3L5Sags1ulNWINFkG_kg8D0lUat7ZFg3Q==',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7',
    'cache-control': 'no-cache',
    'client-version': 'v2.47.29',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://weibo.com/u/7802368987',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'server-version': 'v2025.02.12.2',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'x-xsrf-token': 'sk5nYbHpPyIRnd92aA6SJlKs',
}

params = (
    ('uid', '7802368987'),
    ('page', '24'),
    ('feature', '0'),
)

response = requests.get('https://weibo.com/ajax/statuses/mymblog', headers=headers, params=params, cookies=cookies)
content = response.content.decode("utf-8")
open("test1.json", "w", encoding="utf-8").write(content)
# NB. Original query string below. It seems impossible to parse and
# reproduce query strings 100% accurately so the one below is given
# in case the reproduced version is not "correct".
# response = requests.get('https://weibo.com/ajax/statuses/mymblog?uid=7802368987&page=2&feature=0&since_id=5129215452381490kp2', headers=headers, cookies=cookies)
