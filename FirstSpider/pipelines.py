# -*- coding: utf-8 -*-

import codecs
import json
import pymongo
import MySQLdb
import MySQLdb.cursors
import urllib

from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi

from FirstSpider import settings


class FirstspiderPipeline(object):
    def process_item(self, item, spider):
        return item


# 下载图片
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path
        return item


# Json文件导出
class JsonWithEncodingPipeline(object):

    def __init__(self):
        self.file = codecs.open("article.json", "w", encoding="utf-8")

    # process_item方法返回后，Item进入下一个Pipeline
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


# Scrapy自带的Json文件导出
class JsonExporterPipleline(object):
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(
            self.file,
            encoding="utf-8",
            ensure_ascii=False
        )
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# 同步机制存入MySQL
class MySQLPipeline(object):

    def __init__(self):
        self.conn = MySQLdb.connect(
            settings.MYSQL_HOST,
            settings.MYSQL_USER,
            settings.MYSQL_PASSWORD,
            settings.MYSQL_DBNAME,
            charset="utf8",
            use_unicode=True
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql, params = item.get_insert_sql()
        self.cursor.execute(insert_sql, params)
        return item


# 异步机制存入MySQL
class MySQLTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    # 在初始化时调用：自动从settings获取MySQL相关配置，建立连接池
    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)      # dbpool返回给__init__

    # 使用twisted将mysql插入变成异步执行
    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)  # 交由handle_error处理异常

    # 处理异步插入的异常
    def handle_error(self, failure, item, spider):
        print(failure)

    # 执行数据插入
    def do_insert(self, cursor, item):  # 根据item的SQL语句并插入到MySQL中
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)


class MongoDBPipeline(object):
    def __init__(self):
        self.db = pymongo.MongoClient("localhost", 27017)["IT"]
        self.Jobbole = self.db["Jobbole"]
        self.Zhihu_Question = self.db["Zhihu_Question"]
        self.Zhihu_Answer = self.db["Zhihu_Answer"]
        self.Lagou = self.db["Lagou"]

    def download_cover(self, item):
        url = item["cover"]
        suffix = item["cover"].split(".")[-1]
        name = "{}/{}/{}.{}".format(settings.IMAGES_STORE, item.name, item["_id"], suffix)
        urllib.request.urlretrieve(url, name)

    def process_item(self, item, spider):

        getattr(self, item.name).insert_one(item.get_insert_mongoitem())
        # self.download_cover(item)


# 存入ElasticSearch
class ElasticsearchPipeline(object):
    def process_item(self, item, spider):
        item.insert_to_es()
        return item