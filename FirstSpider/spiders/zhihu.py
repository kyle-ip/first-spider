# -*- coding: utf-8 -*-

import time
import json
import re
import datetime
from PIL import Image
from urllib import parse

import scrapy
from scrapy.http import Request

from FirstSpider.items import ZhihuQuestionItem, ZhihuAnswerItem, ZhihuUserItem, QuestionItemLoader


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['https://www.zhihu.com/']

    custom_settings = {
        "COOKIES_ENABLED": True
    }

    headers = {
        "Host": "www.zhihu.com",
        "authorization": "Bearer Mi4wQUFEQWFTc2lBQUFBY01MZUF5S2FDeGNBQUFCaEFsVk5rUDQ3V1FCTXJRQVRhbmdYMU9rdi1CWXdsQkdDa1otWHVB|1494580682|b446ee779f1d40632a24852a231d54a89bb497d9",
        "Connection:": "keep-alive",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch, br",
        "accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36"
    }

    # 登录页面
    login_url = "https://www.zhihu.com/#signin"
    answer_start_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.badge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

    # 模拟登录帐号
    username = ''
    password = ''
    user_type = 'email'

    # 开始放进去的第一个用户的ID
    start_user = 'fang-liang-0423'
    # 查询粉丝或者关注列表里面的用户需要附带的参数（见Headers的include）
    include_follow = 'data[*].answer_count, articles_count, gender, follower_count, is_followed, is_following, badge[?(type = best_answerer)].topics'
    # 查询个人信息需要附带的参数
    include_userinfo = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,avatar_hue,answer_count,articles_count,pins_count,question_count,columns_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_force_renamed,is_bind_sina,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
    # 获取粉丝列表的url,里面的参数分别是用户的ID，查询参数，offset表示第几页的粉丝或者关注者，limit表示每页的数量，默认20
    followers_url = 'https://www.zhihu.com/api/v4/members/{user_name}/followers?include={include_follow}&offset={offset}&limit={limit}'
    # 获取关注列表的URL，根上面的就差了一个字母
    followees_url = 'https://www.zhihu.com/api/v4/members/{user_name}/followees?include={include_follow}&offset={offset}&limit={limit}'
    # 提取用户信息信息的url
    userinfo_url = 'https://www.zhihu.com/api/v4/members/{user_name}?include={include_userinfo}'


# ------------------------------------------------------- 模拟登录 -------------------------------------------------------

    # 启动爬虫时调用
    def start_requests(self):
        # 访问第一个用户，获取详细信息
        # yield Request(
        #     url=self.userinfo_url.format(
        #         user_name=self.start_user,
        #         include_userinfo=self.include_userinfo
        #     ),
        #     callback=self.get_user_info
        # )

        # 访问第一个用户的粉丝列表
        # yield Request(
        #     url=self.followers_url.format(
        #         user_name=self.start_user,
        #         include_follow=self.include_follow,
        #         offset=0,
        #         limit=20
        #     ),
        #     callback=self.get_followers_parse
        # )

        # 访问第一个用户的关注列表
        # yield Request(
        #     url=self.followees_url.format(
        #         user_name=self.start_user,
        #         include_follow=self.include_follow,
        #         offset=0,
        #         limit=20
        #     ),
        #     callback=self.get_followees_parse
        # )

        # 请求登录页面
        return [Request(
            self.login_url,
            headers=self.headers,
            callback=self.get_captcha
        )]  # 访问登录页面获取XSRF：<input type="hidden" name="_xsrf" value="cf8064fd32bd58e18abe0ec9ce3a44d6"/>

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
            item_loader.add_xpath(
                "watch_user_count",
                "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()"
            )
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")
        question_item = item_loader.load_item()
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

    def get_user_info(self, response):  # 获取用户信息
        data = json.loads(response.text)
        item = ZhihuUserItem()
        for Field in item.fields:  # 可以获取在item里面定义的key值，就是那些locations，employments等
            item[Field] = data.get(Field, "")  # 获取字典里面的值
        yield item

        # 请求该用户的关注列表
        yield Request(
            url=self.followers_url.format(
                user_name=data.get('url_token'),
                include_follow=self.include_follow,
                offset=0,
                limit=20
            ),
            callback=self.get_followers_parse
        )

        # 请求该用户的粉丝列表
        yield Request(
            url=self.followees_url.format(
                user_name=data.get('url_token'),
                include_follow=self.include_follow,
                offset=0,
                limit=20
            ),
            callback=self.get_followees_parse
        )

    # 获取粉丝信息
    def get_followers_parse(self, response):
        try:        # 防止有些用户没有粉丝
            followers_data = json.loads(response.text)
            try:    # 防止有些用户没有url_token
                if followers_data.get('data'):  # data里面是一个由字典组成的列表，每个字典是粉丝的相关信息
                    for one_user in followers_data.get('data'):
                        user_name = one_user['url_token']   # 提取url_token然后访问他的详细信息
                        yield Request(
                            url=self.userinfo_url.format(
                                user_name=user_name,
                                include_userinfo=self.include_userinfo
                            ),
                            callback=self.get_user_info
                        )   # 将所有粉丝或者关注者的url_token提取出来，放进一开始构造的用户详细信息的网址里面提取信息
                if 'paging' in followers_data.keys() and followers_data.get('paging').get('is_end') is False:
                    yield Request(
                        url=followers_data.get('paging').get('next'),
                        callback=self.get_followers_parse
                    )
            except Exception as e:
                print(e, '该用户没有url_token')
        except Exception as e:
            print(e, ' 该用户没有粉丝')


# 包含yield的函数为生成器函数，在生成值后会自动挂起并暂停他们的执行和状态，本地变量将保存状态信息
# 对页面未处理完成使用yield，处理完成使用return
