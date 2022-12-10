import base64
import datetime
import hashlib
import json
import os
import random
import sys
import threading
import time

import requests
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad


def printf(text):
    ti = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f'[{ti}]: {text}')
    sys.stdout.flush()

def desEn(content, key):
    key = key[:8].encode('utf-8')
    content = content.encode('utf-8')
    cipher = DES.new(key=key, mode=DES.MODE_ECB)
    content = pad(content, block_size=DES.block_size, style='pkcs7')
    res = cipher.encrypt(content)
    return base64.b64encode(res)

def desDe(content, key):
    key = key[:8].encode('utf-8')
    content = base64.b64decode(content)
    cipher = DES.new(key=key, mode=DES.MODE_ECB)
    res = cipher.decrypt(content)
    res = unpad(res, DES.block_size, style='pkcs7')
    return res.decode('utf-8')

def generate_random_str(randomlength=16):
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str

def getTimestamp():
    return int(round(time.time() * 1000))

def rcape(v):
    if len(v) != 2:
        return '0'+v
    return v

def getJsonId():
    global start_time
    url = 'https://gz-cdn.xiaoyisz.com/mengniu_bainai/game_configs/prod_v1/game_configs.json?v=1670228082180'
    res = requests.get(url=url, headers=head).json()
    month = datetime.datetime.now().strftime('%m')
    day = datetime.datetime.now().strftime('%d')
    day = rcape(str(int(day) - 1))

    for item in res['activity_data']:
        result_id = item['result_id']
        result_id = result_id.replace('result_', '')
        json_id = item['json_id']
        if result_id == (month+day):
            reward_Num = item['reward_Num']
            start_time = item['start_time']
            printf(f'今日可抢牛奶数量：{reward_Num}')
            return json_id
    return ''

def getRKSign(timestamp, nonce):
    md5Str = f'clientKey={clientKey}&clientSecret={clientSecret}&nonce={nonce}&timestamp={timestamp}'
    return hashlib.md5(md5Str.encode('utf-8')).hexdigest().upper()

def getRk():
    timestamp = getTimestamp()
    nonce = generate_random_str(16)
    sign = getRKSign(timestamp, nonce)
    url = f'{domain}/mengniu-world-cup/mp/api/user/baseInfo?timestamp={timestamp}&nonce={nonce}&signature={sign}'
    res = requests.get(url=url, headers=head).json()
    printf(res)
    try:
        return res['data']['rk']
    except Exception:
        raise Exception('获取账号rk失败，该token已经触发风控机制，请重新抓包获取新token')

def getMilkSign(requestId, timestamp, rk):
    md5Str = f'requestId={requestId}&timestamp={timestamp}&key={rk}'
    return hashlib.md5(md5Str.encode('utf-8')).hexdigest()

def skillMilk(rk, jsonId):
    timestamp = getTimestamp()
    requestId = generate_random_str(32)
    nonce = generate_random_str(16)
    signature = getRKSign(timestamp, nonce)
    sign = getMilkSign(requestId, timestamp, rk)
    url = f'{domain}/mengniu-world-cup-1122{updateUrl}?timestamp={timestamp}&nonce={nonce}&signature={signature}&jsonId={jsonId}'
    head['sign'] = sign
    head['timestamp'] = str(timestamp)
    head['requestId'] = requestId
    res = requests.get(url=url, headers=head).text
    printf(res)

def isStart():
    timestamp = getTimestamp()
    current_time = getTimestamp()
    if current_time >= (start_time - preTime):
        return True
    else:
        return False

if __name__ == '__main__':
    try:
        with open('./config.json', 'r') as c:
            rdConfigStr = c.read()
        config = json.loads(rdConfigStr)
    except Exception as e:
        printf(f'加载配置文件异常：{str(e)}')
        os.system('pause')

    '''
    time无需管 服务器获取
    '''
    start_time = 0
    domain = config['domain']

    '''
    token是小程序包的请求头的Authorization: 
    '''
    token = config['token']
    desKey = config['desKey']
    clientKey = config['clientKey']
    clientSecret = config['clientSecret']
    updateUrl = config['updateUrl']
    '''
    请求头
    '''
    head = {
        'User-Agent': config['User-Agent'],
        'Referer': config['Referer'],
        'content-type': 'application/json',
        'Authorization': token
    }

    '''
    账号的rk 自动获取
    '''
    rk = getRk()
    '''
    抢多少次最大24 多了触发风控机制 导致无法获取rk 所有接口返回{"code":500,"message":"非领奶时间"} 触发风控机制后需要更新toekn才能恢复正常
    '''
    threadNumber = config['threadNumber']
    '''
    提交几秒开枪（单位毫秒）
    如 2000 就是 8:59:58秒开枪
    '''
    preTime = config['preTime']

    rk = desDe(rk, desKey)
    jsonId = getJsonId()
    time.sleep(1)
    tdList = []
    while True:
        if isStart():
            for i in range(threadNumber):
                try:
                    skillMilk(rk, jsonId)
                except Exception as e:
                    printf(f'抢奶异常：{str(e)}')
            break
        else:
            printf("等待开始...")

    os.system('pause')


