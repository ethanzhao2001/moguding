import urllib.parse
import hashlib
import hmac
import requests
import json
import time
import pendulum
from hashlib import md5
from fake_useragent import UserAgent
import base64
# pip3 install pycryptodome
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
session = requests.session()
ua = UserAgent()


def send_dingding(text: str, webhook: str, key: str):
    sign_data = send_sign(key)
    webhook = f'{webhook}&sign={sign_data["sign"]}&timestamp={sign_data["timestamp"]}'
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": text
        },
    }
    r = requests.post(webhook, headers=headers, data=json.dumps(data))
    print(r.text)


def send_sign(key: str):
    timestamp = str(round(time.time() * 1000))
    secret = key
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc,
                         digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    sign_data = {
        'sign': sign,
        'timestamp': timestamp,
    }
    return (sign_data)


def get_proxy():
    url = "http://127.0.0.1:5010/get"
    res_json = session.get(url=url).json()
    if res_json["https"]:
        return {
            "https": "https://" + res_json["proxy"]
        }
    else:
        return {
            "http": "http://" + res_json["proxy"]
        }


def getToken(username: str, password: str, login_type: str = "android", t: str = str(int(time.time()*1000))):
    url = "https://api.moguding.net:9000/session/user/v3/login"
    data = {
        "password": encrypt("23DbtQHR2UMbH6mJ", password),
        "phone": encrypt("23DbtQHR2UMbH6mJ", username),
        "loginType": login_type,
        "t": encrypt("23DbtQHR2UMbH6mJ", t)
    }
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "user-agent": ua.chrome
    }
    res = session.post(url=url, data=json.dumps(data), headers=headers)
    if res.json()["code"] == 500:
        print(res.json()["msg"])
        exit()
    else:
        sign = get_sign(
            text=res.json()["data"]["userId"] + res.json()["data"]["userType"])
        return res.json()["data"]["token"], sign, res.json()["data"]["userId"]


def encrypt(key, text):
    aes = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    pad_pkcs7 = pad(text.encode('utf-8'), AES.block_size, style='pkcs7')
    # 加密函数,使用pkcs7补全
    res = aes.encrypt(pad_pkcs7)
    msg = res.hex()
    return msg


def get_sign(text: str):
    s = text + "3478cbbc33f84bd00d75d7dfa69e0daa"
    return md5(s.encode("utf-8")).hexdigest()


def get_plan_id(token: str, sign: str):
    url = "https://api.moguding.net:9000/practice/plan/v3/getPlanByStu"
    data = {
        "state": ""
    }
    headers = {
        'roleKey': 'student',
        "authorization": token,
        "sign": sign,
        "content-type": "application/json; charset=UTF-8",
        "user-agent": ua.chrome
    }
    res = session.post(url=url, data=json.dumps(data), headers=headers)
    return res.json()["data"][0]["planId"]


def save(user_id: str, authorization: str, plan_id: str, country: str, province: str, city: str,
         address: str, save_type: str = "START", description: str = "",
         device: str = "Android", latitude: str = None, longitude: str = None):
    text = device + save_type + plan_id + user_id + address
    headers = {
        'roleKey': 'student',
        "user-agent": ua.chrome,
        "sign": get_sign(text=text),
        "authorization": authorization,
        "content-type": "application/json; charset=UTF-8"
    }
    data = {
        "country": country,
        "address": address,
        "province": province,
        "city": city,
        "latitude": latitude,
        "description": description,
        "planId": plan_id,
        "type": save_type,
        "device": device,
        "longitude": longitude
    }
    url = "https://api.moguding.net:9000/attendence/clock/v2/save"
    res = session.post(url=url, headers=headers, data=json.dumps(data))
    if res.json()["code"] == 200:
        print("打卡成功！\n")
        #send_dingding('打卡成功！\n' + res.text, 'webhook', '加签')#钉钉推送，不需要就注释掉
    else:
        print("出错了：\n" + res.json() + "\n")


def main(phone="",
         pwd="",
         logintype="android",
         country="中国",
         province="",
         city="",
         address="",
         description="",
         latitude="",
         longitude=""):
    print(pendulum.now().to_datetime_string() + " 账号：" + phone + " 开始打卡...\n")
    if int(pendulum.now().to_time_string()[:2]) <= 9:
        save_type = "START"
    else:
        save_type = "END"
    try:
        session.proxies.update(get_proxy())
        auth_token, sign_value, user_id = getToken(
            username=phone, password=pwd, login_type=logintype)
        plan_id = get_plan_id(token=auth_token, sign=sign_value)
        save(user_id=user_id, authorization=auth_token, plan_id=plan_id, country=country, province=province, city=city,
             address=address, save_type=save_type, description=description,
             device=logintype.capitalize(), latitude=latitude, longitude=longitude)
    except:
        auth_token, sign_value, user_id = getToken(
            username=phone, password=pwd, login_type=logintype)
        plan_id = get_plan_id(token=auth_token, sign=sign_value)
        save(user_id=user_id, authorization=auth_token, plan_id=plan_id, country=country, province=province, city=city,
             address=address, save_type=save_type, description=description,
             device=logintype.capitalize(), latitude=latitude, longitude=longitude)


if __name__ == "__main__":
    time.sleep(1)
    main(
        phone="",  # 账号/手机号
        pwd="",  # 密码
        logintype="android",  # 打卡设备类型
        country="中国",  # 国家
        province="",  # 省
        city="",  # 市
        address="",  # 详细地址，打卡页面输出显示
        description="",  # 打卡描述
        latitude="",  # 纬度
        longitude=""  # 经度
    )
