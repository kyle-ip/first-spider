# FirstSpider
 我的第一个爬虫项目（基于Python3.5.3, Scrapy 1.3.3），目标是爬取伯乐在线的文章、知乎网上的问答和拉勾网上的职位信息。
 
 目前支持把数据写入Json文件、MySQL、MongoDB，并已定义ElasticSearch数据模型，为开发搜索网站做准备。
 
 
 
 
 
 
 ## 使用方法
  1、安装环境依赖包（不同版本操作系统安装方法有差异，见网上具体解决方案）：<pre><code>pip install -r requirements.txt</code></pre>
  2、项目目录下：<pre><code>python main.py</code></pre>
  也可以指定运行某个爬虫：
  <pre><code>scrapy crawl zhihu</code></pre>
