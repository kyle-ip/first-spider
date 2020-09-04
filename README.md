# first-spider
 我的第一个爬虫项目（基于 Python3.5.3, Scrapy 1.3.3），目标是爬取伯乐在线的文章、知乎网上的问答和拉勾网上的职位信息；目前支持把数据写入 Json 文件、MySQL、MongoDB，并已定义 ElasticSearch 数据模型，为开发 [搜索网站](https://github.com/yipwinghong/SearchEngine) 做准备。

 


 ## 使用方法
安装环境依赖包（不同版本操作系统安装方法有差异，见网上具体解决方案）：

```shell
pip install -r requirements.txt
```

项目目录下执行：

```shell
python main.py
```

也可以指定运行某个爬虫：

```shell
scrapy crawl zhihu
```

