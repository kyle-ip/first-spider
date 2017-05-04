# -*- coding: utf-8 -*-

import random
from multiprocessing import Pool
import pymongo
import requests

from scrapy.selector import Selector

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36",
}
page = "http://www.xicidaili.com/nn/{}"
client = pymongo.MongoClient("localhost", 27017)
firstspider = client["firstspider"]
proxy_ip_pool = firstspider["proxy_ip_pool"]


def crawl_ip(page):
    res = requests.get(page, headers=headers)
    selector = Selector(text=res.text)
    is_end = len(selector.css("span.next_page").extract())
    if not is_end:
        all_trs = selector.css("#ip_list tr")
        ip_list = []
        for tr in all_trs[1:]:
            speed = tr.css(".bar::attr(title)").extract()[0]
            speed = float(speed.split("秒")[0]) if speed else None
            all_texts = tr.css("td::text").extract()
            ip, port, proxy_type = all_texts[0], all_texts[1], all_texts[5],
            ip_list.append((ip, port, proxy_type, speed))
            proxy_ip_pool.insert_one({
                "ip": ip,
                "port": port,
                "proxy_type": proxy_type,
                "speed": speed,
            })
            print("{}\t{}\t{}\t{}".format(ip, port, proxy_type, speed))


def crawl_all_ips(end):
    pool = Pool()
    pool.map(crawl_ip, (page.format(str(page_num)) for page_num in range(1, end)))


def get_ip():
    i = proxy_ip_pool.find().sort("speed", pymongo.ASCENDING).limit(int(random.random()*100))[int(random.random()*10)]
    ip, port = i["ip"], i["port"]
    return "http://{}:{}".format(ip, port)


def test_ip(i):
    http_url = "http://www.baidu.com"
    proxy_url = "http://{0}:{1}".format(i["ip"], i["port"])
    proxies = {"http": proxy_url}
    try:
        code = requests.get(http_url, proxies=proxies, headers=headers).status_code
    except:
        pass
    else:
        if 200 <= code <= 300:
            print("{}\t{}\t{}".format(i["ip"], i["port"], i["proxy_type"]))
    # return "OK" if 200 <= code <= 300 else code


def delete_ip(ip):
    for i in proxy_ip_pool.find():
        if i["ip"] == ip:
            proxy_ip_pool.delete_one({"ip": i["ip"]})


if __name__ == '__main__':
    # crawl_all_ips(2000)
    # for ip in proxy_ip_pool.find().sort("speed", pymongo.ASCENDING).limit(100):
    #     print("{}\t{}\t{}".format(ip["ip"], ip["port"], ip["speed"]))

    # print(test_ip("111.155.124.70", "8123"))

    ip_list = [ip for ip in proxy_ip_pool.find().sort("speed", pymongo.ASCENDING)]
    pool = Pool()
    pool.map(test_ip, ip_list)



'''
    221.216.94.77   808     HTTP

'''

'''
    MySQL中随机取数据的方法：
        select ip, port from proxy_ip
        order by rand()
        limit 1
    MySQL中删除数据的方法：
        delete from proxu_ip
        where ip=...
        
'''