import time

import requests

cookies = {
}

headers = {

}

params = {

}
max_id = ""
count=0
while True:
    if max_id:
        params["max_id"] = max_id
    response = requests.get('https://weibo.com/ajax/statuses/buildComments',
                            headers=headers, params=params, cookies=cookies)
    data = response.json()
    max_id = data["max_id"]
    comms = data["data"]
    if comms:
        message = comms[0]["text_raw"]
    else:
        message = "未获取到评论"
    print(data["ok"], len(comms), max_id, data["trendsText"], message)
    count+=1
    time.sleep(1)