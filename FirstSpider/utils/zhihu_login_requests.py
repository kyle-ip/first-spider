# -*- coding: utf-8 -*-

import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib

import time
from PIL import Image
import re
from bs4 import BeautifulSoup
import urllib

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print ("cookie未能加载")

agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
headers = {
    "HOST":"www.zhihu.com",
    "Referer": "https://www.zhizhu.com",
    'User-Agent': agent
}


def is_login():
    # 通过个人中心页面返回状态码来判断是否为登录状态
    inbox_url = "https://www.zhihu.com/question/56250357/answer/148534773"
    response = session.get(inbox_url, headers=headers, allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def get_xsrf():
    # 获取xsrf code
    response = session.get("https://www.zhihu.com", headers=headers)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text)
    if match_obj:
        return (match_obj.group(1))
    else:
        return ""


def get_captcha():
    t = str(int(time.time()*1000))
    captcha_url = "https://www.zhihu.com/captcha.gif?r={}&type=login".format(t)
    t = session.get(captcha_url, headers=headers)
    with open("captcha", "wb") as f:
        f.write(t.content)
        f.close()
    try:
        im = Image.open("captcha")
        im.show()
        im.close()
    except:
        pass
    captcha = input("输入验证码\n>")
    return captcha


def get_index():
    response = session.get("https://www.zhihu.com", headers=headers)
    with open("index_page.html", "wb") as f:
        f.write(response.text.encode("utf-8"))
    print("ok")


def zhihu_login(account, password):
    # 知乎登录
    if re.match("^1\d{10}",account):
        print ("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": account,
            "password": password,
            "captcha": get_captcha(),
        }
    else:
        if "@" in account:
            # 判断用户名是否为邮箱
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "email": account,
                "password": password,
                "captcha": get_captcha(),
            }
    response_text = session.post(post_url, data=post_data, headers=headers)
    session.cookies.save()


def get_image_from(pic):
    try:
        pic_url = pic['cover']
        pic_name = '{}/{}.{}'.format('images', pic['id'], 'jpg')
        urllib.urlretrieve(pic_url, pic_name)
    except Exception as e:
        print('{}\t{}'.format(pic['id'], e))


def get_question():
    url = "https://www.zhihu.com/question/50333521/answer/159028756"
    soup = BeautifulSoup(session.get(url, headers=headers).text, 'lxml')
    images = soup.select(".CopyrightRichText-richText img")
    for i in images:
        image_url = i.get('data-original')
        print(image_url)

get_question()


