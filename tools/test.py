# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from scrapy.selector import Selector

# browser = webdriver.Chrome(executable_path="C:/Users/Administrator/Desktop/chromedriver.exe")
#
#
# browser.get("http://weibo.com/login.php")
# time.sleep(5)      # 避免页面未加载完就执行下一步

# # 模拟登录
# browser.find_element_by_css_selector("#loginname").send_keys("15622262330")
# browser.find_element_by_css_selector(".info_list.password input[node-type='password']").send_keys("LKJHGFDSA")
# browser.find_element_by_css_selector(".info_list.login_btn span[node-type='submitStates']").click()
#
#
# browser.get("http://www.dgtle.com/")
# # 模拟页面滚动
# for i in range(3):
#     browser.execute_script(
#         "window.scrollTo(0, document.body.scrollHeight); "
#         "var lenOfPage=document.body.scrollHeight; "
#         "return lenOfPage;"
#     )
#     time.sleep(2)

# browser.quit()

# 不加载图片
# chrome_opt = webdriver.ChromeOptions()
# prefs = {"profile.managed_default_content_settings.images": 2}
# chrome_opt.add_experimental_option("prefs", prefs)
# browser = webdriver.Chrome(executable_path="C:/Users/Administrator/Desktop/chromedriver.exe", chrome_options=chrome_opt)
# browser.get("https://www.taobao.com")


browser = webdriver.Chrome(executable_path="...")
browser.get("https://www.taobao.com")
browser.quit()