# -*- coding: utf-8 -*-

from selenium import webdriver

import time
import scrapy
from scrapy.http import Request
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

from urllib import parse

from FirstSpider.utils.common import get_md5
from FirstSpider.items import ArticleItemLoader, JobboleArticleItem


class JobboleSpider(scrapy.Spider):
    name = "jobbole"
    allowed_domains = ["blog.jobbole.com"]
    start_urls = ['http://blog.jobbole.com/all-posts/']

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36"
    }

    # # 初始化时开启所有爬虫使用的chrome窗口
    # def __init__(self):
    #     self.browser = webdriver.Chrome(executable_path="C:/Users/Administrator/Desktop/chromedriver.exe")
    #     super(JobboleSpider, self).__init__()
    #     dispatcher.connect(self.spider_closed, signals.spider_closed)
    #
    # # 爬虫退出时关闭Chrome
    # def spider_closed(self, spider):
    #     print("Spider closed.")
    #     self.browser.quit()

    # # 收集所有404的URL及数目
    # handle_httpstatus_list = [404, ]
    #
    # def __init__(self):
    #     self.fail_urls = []
    #     super(JobboleSpider, self).__init__()
    #     dispatcher.connect(self.handle_spider_closed, signals.spider_closed)
    #
    # # 爬虫停止时把所有的404 url连接保存
    # def handle_spider_closed(self, spider, reason):
    #     self.crawler.stats.set_value("failed_urls", ",".join(self.fail_urls))

    # 从列表页中提取所有文章详细页
    def parse(self, response):
        #
        # # 处理404页面
        # if response.status == 404:
        #     self.fail_urls.append(response.url)
        #     self.crawler.stats.inc_value("failed_url")

        # 解析列表页中的所有文章url，交给scrapy下载并解析
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(
                url=parse.urljoin(response.url, post_url),
                meta={"front_image_url": image_url},
                headers=self.headers,
                callback=self.parse_detail
            )
            # #archive > div.navigation.margin-20 > a.next.page-numbers

        # 提取下一页并交给scrapy继续下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(
                url=parse.urljoin(response.url, next_url),
                headers=self.headers,
                callback=self.parse
            )

    # 解析文章详细页
    def parse_detail(self, response):

        # 使用指定的Item启用ItemLoader
        item_loader = ArticleItemLoader(item=JobboleArticleItem(), response=response)
        front_image_url = response.meta.get("front_image_url")

        # 解析详细页
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_css("created_time", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [front_image_url])
        item_loader.add_css("voteup_count", ".vote-post-up h10::text")
        item_loader.add_css("comments_count", "a[href='#article-comment'] span::text")
        item_loader.add_css("fav_count", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")

        # 装载item并返回
        article_item = item_loader.load_item()
        yield article_item
