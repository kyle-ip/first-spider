# -*- coding: utf-8 -*-

import time
import json
import re
import datetime
from PIL import Image
from urllib import parse

import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader

from FirstSpider.items import ZhihuQuestionItem, ZhihuAnswerItem, QuestionItemLoader


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['https://www.zhihu.com/']

    custon_settings = {
        "COOKIES_ENABLED": True
    }

    login_url = "https://www.zhihu.com/#signin"
    answer_start_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.badge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36"
    }

    username = '418704861@qq.com'
    password = 'K418704861'
    user_type = 'email'


# ------------------------------------------------------- 模拟登录 -------------------------------------------------------

    # 启动爬虫时调用：请求登录页面
    def start_requests(self):
        # 访问登录页面获取XSRF：<input type="hidden" name="_xsrf" value="cf8064fd32bd58e18abe0ec9ce3a44d6"/>
        return [Request(
            self.login_url,
            headers=self.headers,
            callback=self.get_captcha
        )]

    # 获取xsrf、get请求验证码页面
    def get_captcha(self, response):
        _xsrf = response.css("form input[name='_xsrf']::attr('value')").extract_first("")
        if _xsrf:
            post_data = {
                "_xsrf": _xsrf,
                "{}".format(self.user_type): self.username,
                "password": self.password,
                "captcha": "",
            }
            num = str(int(time.time()*1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={}&type=login".format(num)
            yield Request(      # 使用yield能保持当前访问状态，使用相同的cookie建立session
                captcha_url,
                headers=self.headers,
                meta={"post_data": post_data},
                callback=self.login
            )

    # 登录，post请求登录
    def login(self, response):
        captcha = "captcha.jpg"
        with open(captcha, "wb") as f:
            f.write(response.body)
        try:
            Image.open(captcha).show()
        except:
            pass
        post_data = response.meta.get("post_data", {})
        post_url = "https://www.zhihu.com/login/{}".format(self.user_type)
        post_data["captcha"] = input("Please input the captcha: ")
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]

    # 判断是否登录，登录则从start_urls获取url交给parse解析，否则退出爬虫
    def check_login(self, response):
        response_text = json.loads(response.text)
        msg = response_text.get("msg", "")
        if msg == "登录成功":
            print(msg)
            for url in self.start_urls:     # scrapy默认对request的URL去重，dont_filter表示URL不参与去重
                yield Request(
                    url,
                    dont_filter=True,
                    headers=self.headers
                )  # 没有指定callback, 则请求相应返回到parse方法


# ---------------------------------------------------- 爬取问题和答案 ----------------------------------------------------

    # 解析页面中的问题URL
    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]   # 动态补全内链
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)     # 过滤出以https开头的url
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)     # 提取url中的question id

            # 深度优先
            if match_obj:   # 如果提取到问题的URL则交由parse_question解析
                question_url = match_obj.group(1)
                yield Request(                  # url：'https://www.zhihu.com/question/58494299/answer/160258621'
                    question_url,               # question_url：'https://www.zhihu.com/question/58494299'
                    headers=self.headers,
                    callback=self.parse_question
                )
            else:   # 如果该URL不是问题页面，则请求该URL，分析该页面中是否有其他问题URL
                yield Request(
                    url,                        # url：'https://www.zhihu.com/'
                    headers=self.headers,
                    callback=self.parse
                )

    # 从问题页面中提取question item
    def parse_question(self, response):
        match_obj = re.match(".*?(\d+).*", response.url)
        question_id = int(match_obj.group(1)) if match_obj else "0"
        item_loader = QuestionItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_value("url", response.url)
        item_loader.add_value("question_id", question_id)

        # 新版本的页面（其余字段在新旧页面的样式不同）
        if "QuestionHeader-title" in response.text:     # 默认只处理新版本（旧版本页面暂略）
            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_css("answers_count", ".List-headerText span::text")
            item_loader.add_css("comments_count", ".QuestionHeader-actions button::text")
            item_loader.add_css("watch_user_count", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

        # 旧版本的页面
        else:   # xpath比css的优势是可以使用逻辑或
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_css("answers_count", "#zh-question-answer-num::text")
            item_loader.add_css("comments_count", "#zh-question-meta-wrap a[name='addcomment']::text")
            item_loader.add_xpath("watch_user_count",
                                  "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")
        question_item = item_loader.load_item()
        pass
        yield question_item     # 1、把question item传给pipeline

        yield Request(          # 2、获取该问题页面下的答案
            self.answer_start_url.format(question_id, 20, 0),
            headers=self.headers,
            callback=self.parse_answer
        )

    # 从问题页面中提取answer item
    def parse_answer(self, response):
        answers = json.loads(response.text)     # 一个页面的JSON包含多条评论

        # 获取一个页面中的答案数据，JSON数据可以直接获取，不需要使用css或者xpath来提取，也不需要使用Item Loader
        for answer in answers["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["answer_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["voteup_count"] = answer["voteup_count"]
            answer_item["comments_count"] = answer["comment_count"]
            answer_item["created_time"] = answer["created_time"]
            answer_item["updated_time"] = answer["updated_time"]

            yield answer_item   # 1、把answer item传给pipeline

        is_end = answers["paging"]["is_end"]
        next_url = answers["paging"]["next"]
        if not is_end:          # 2、判断是否已到最后一页，还没则继续获取下一页来解析
            yield Request(
                next_url,
                headers=self.headers,
                callback=self.parse_answer
            )

# 包含yield的函数为生成器函数，在生成值后会自动挂起并暂停他们的执行和状态，本地变量将保存状态信息
# 对页面未处理完成使用yield，处理完成使用return
