# -*- coding: utf-8 -*-

import re
import datetime
import scrapy
from w3lib.html import remove_tags

from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from elasticsearch_dsl.connections import connections
import redis

from FirstSpider.settings import SQL_DATETIME_FORMAT
from FirstSpider.utils.common import extract_num
from FirstSpider.models.es_type import ArticleType, QuestionType, JobType


# --------------------------------------------------- 伯乐在线文章item ---------------------------------------------------
# redis_cli = redis.StrictRedis()
es = connections.create_connection(ArticleType._doc_type.using)


def get_content(value):
    return remove_tags(value)


# 根据字符串生成搜索建议数组
def gen_suggests(index, info_tuple):
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter': ["lowercase"]}, body=text)
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1])
            new_words = anylyzed_words - used_words
        else:
            new_words = set()
        if new_words:
            suggests.append({"input": list(new_words), "weight": weight})

    return suggests


# 转换时间格式
def date_convert(value):
    try:
        created_time = datetime.datetime.strftime(value, "%Y/%m/%d").date()
    except:
        created_time = datetime.datetime.now().date()
    return created_time


# 取字符串中的数字
def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    nums = int(match_re.group(1)) if match_re else 0
    return nums


# 返回原值
def return_value(value):
    return value


# 去除tags中的“评论”
def remove_comment_tags(value):
    return "" if "评论" in value else value


# 连接tags
def join_tags(value):
    return ','.join([i for i in value if i])


# 继承ItemLoader，重写其output_processor方法
# ItemLoader默认是以list的类型存放，要想取列表的字段可以修改output_processor
class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()  # 默认取列表的第一项


# input_processor：输入预处理（装载到Item前的处理）
# output_procrssor：输出预处理（返回给Pipeline前的处理）
class JobboleArticleItem(scrapy.Item):
    name = "Jobbole"

    title = scrapy.Field()
    created_time = scrapy.Field(
        input_processor=MapCompose(date_convert)
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(                 # 配置了ImagePipelines，图片url字段类型就必须为list
        output_processor=MapCompose(return_value)   # 不能使用default_output_procssor，而另写一个函数覆盖
    )
    front_image_path = scrapy.Field()
    comments_count = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_count = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    voteup_count = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field(
        input_processor=MapCompose(get_content)
    )

    def get_insert_sql(self):
        insert_sql = """
                    insert into jobbole(
                    title, url, url_object_id, created_time, 
                    fav_count, front_image_url, front_image_path,
                    voteup_count, comments_count, tags, content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                    ON DUPLICATE KEY UPDATE content=VALUES(fav_count)
                """

        front_image_url = self["front_image_url"][0] if self["front_image_url"] else ""

        params = (
            self["title"], self["url"], self["url_object_id"],
            self["created_time"], self["fav_count"], front_image_url,
            self["front_image_path"], self["voteup_count"], self["comments_count"],
            self["tags"], self["content"]
        )

        return insert_sql, params

    def get_insert_mongoitem(self):
        item = {}
        item["title"] = self["title"]
        item["tags"] = self["tags"]
        item["_id"] = self["url_object_id"]
        item["created_time"] = str(self["created_time"])
        item["url"] = self["url"]
        item["front_image_url"] = self["front_image_url"]
        # item["front_image_path"] = self["front_image_path"]
        item["fav_count"] = self["fav_count"]
        item["voteup_count"] = self["voteup_count"]
        item["content"] = remove_tags(self["content"]).strip()
        item["comments_count"] = self["comments_count"]
        return item

    def insert_to_es(self):
        article = ArticleType()
        article.title = self['title']
        article.created_time = self["created_time"]
        article.content = self["content"]
        article.url = self["url"]
        article.tags = self["tags"]
        article.meta.id = self["url_object_id"]
        article.suggests = gen_suggests(ArticleType._doc_type.index, ((article.title, 10), (article.tags, 7)))
        article.save()

        # redis_cli.incr("jobbole_count")
        return


# ---------------------------------------------- 知乎问题、答案、用户信息item ----------------------------------------------
class QuestionItemLoader(ItemLoader):
    default_output_processor = TakeFirst()  # 默认取列表的第一项


def join_topics(value):
    return ','.join([i for i in value if i])


def get_watch_user_count(value):
    return int(value[0])


def get_click_count(value):
    return int(value[1]) if len(value) == 2 else 0


class ZhihuQuestionItem(scrapy.Item):
    name = "Zhihu_Question"

    question_id = scrapy.Field()
    topics = scrapy.Field(
        # input_processor=MapCompose(return_value),
        output_processor=Join(",")
    )
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field(
        input_processor=MapCompose(get_content)
    )
    answers_count = scrapy.Field(
        output_processor=MapCompose(get_nums)
    )
    comments_count = scrapy.Field(
        output_processor=MapCompose(get_nums)
    )
    click_count = scrapy.Field(
        output_processor=MapCompose(get_click_count)
    )
    watch_user_count = scrapy.Field(
        output_processor=MapCompose(get_watch_user_count)
    )
    crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

    def get_insert_sql(self):
        question_id = self["question_id"]
        topics = self["topics"]
        url = self["url"]
        title = self["title"]
        content = self["content"]
        answers_count = self["answers_count"]
        comments_count = self["comments_count"]
        watch_user_count = self["watch_user_count"]
        click_count = self["click_count"]
        crawl_time = self["crawl_time"]


        insert_sql = """
            insert into question(
            question_id, topics, url, title, content, 
            answers_count, comments_count, watch_user_count, 
            click_count, crawl_time
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), 
            answers_count=VALUES(answers_count), 
            comments_count=VALUES(comments_count),
            watch_user_count=VALUES(watch_user_count), 
            click_count=VALUES(click_count)
        """

        params = (
            question_id, topics, url,
            title, content, answers_count,
            comments_count, watch_user_count,
            click_count, crawl_time
        )

        return insert_sql, params

    def insert_to_es(self):
        question = QuestionType()
        question.title = self['title']
        question.content = self["content"]
        question.url = self["url"]
        question.tags = self["topics"]
        question.meta.id = self["question_id"]
        question.suggests = gen_suggests(QuestionType._doc_type.index, ((question.title, 10), (question.tags, 7)))
        question.save()

        # redis_cli.incr("jobbole_count")
        return


class ZhihuAnswerItem(scrapy.Item):
    name = "Zhihu_Answer"

    answer_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    voteup_count = scrapy.Field()
    comments_count = scrapy.Field()
    created_time = scrapy.Field()
    updated_time = scrapy.Field()
    crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

    def get_insert_sql(self):
        created_time = datetime.datetime.fromtimestamp(self["created_time"]).strftime(SQL_DATETIME_FORMAT)
        updated_time = datetime.datetime.fromtimestamp(self["updated_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["answer_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["voteup_count"],
            self["comments_count"], created_time, updated_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        insert_sql = """
            insert into answer(
            answer_id, url, question_id, author_id, 
            content, voteup_count, comments_count,
              created_time, updated_time, crawl_time
              ) 
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE 
              content=VALUES(content), 
              comments_count=VALUES(comments_count), 
              voteup_count=VALUES(voteup_count),
              updated_time=VALUES(updated_time)
        """

        return insert_sql, params


class ZhihuUserItem(scrapy.Item):
    answer_count = scrapy.Field()               # 回答数量
    articles_count = scrapy.Field()             # 写过的文章数
    follower_count = scrapy.Field()             # 粉丝数量
    following_count = scrapy.Field()            # 关注了多少人
    educations = scrapy.Field()                 # 教育背景
    description = scrapy.Field()                # 个人描述
    locations = scrapy.Field()                  # 所在地
    url_token = scrapy.Field()                  # 知乎给予的每个人用户主页唯一的ID
    name = scrapy.Field()                       # 用户昵称
    employments = scrapy.Field()                # 工作信息
    business = scrapy.Field()                   # 一些工作或者商业信息的合集
    user_type = scrapy.Field()                  # 用户类型，可以是个人，也可以是团体等等
    headline = scrapy.Field()                   # 个人主页的标签
    voteup_count = scrapy.Field()               # 获得的赞数
    thanked_count = scrapy.Field()              # 获得的感谢数
    favorited_count = scrapy.Field()            # 被收藏次数
    avatar_url = scrapy.Field()                 # 头像URl


# -------------------------------------------------- 拉勾网招聘信息item --------------------------------------------------

# 去除所有“/”
def replace_splash(value):
    return value.replace("/", "")


# 去除所有空格、换行符
def handle_strip(value):
    return value.replace('\n', '').strip()


# 去除所有空格、换行符
def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)


class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item):
    name = "Lagou"

    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(replace_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor=MapCompose(handle_strip, get_content),
    )
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_name = scrapy.Field(
        input_processor=MapCompose(handle_strip),
    )
    company_url = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(
            title, url, salary, job_city, 
            work_years, degree_need, job_type, 
            publish_time, job_advantage, 
            job_desc, job_addr, company_url, 
            company_name, job_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE 
            job_desc=VALUES(job_desc)
        """

        job_id = extract_num(self["url"])
        params = (
            self["title"], self["url"], self["salary"],
            self["job_city"], self["work_years"], self["degree_need"],
            self["job_type"], self["publish_time"], self["job_advantage"],
            self["job_desc"], self["job_addr"], self["company_url"],
            self["company_name"], job_id
        )

        return insert_sql, params

    def insert_to_es(self):
        job = JobType()
        job.title = self['title']
        job.content = "「" + self["company_name"] + "」" + self["job_desc"]
        job.url = self["url"]
        job.tags = self["job_city"] + ',' + self["work_years"] + ',' + self["job_type"]
        job.meta.id = self["url_object_id"]
        job.suggests = gen_suggests(JobType._doc_type.index, ((job.title, 10), (job.tags, 7)))
        job.save()

        # redis_cli.incr("jobbole_count")
        return