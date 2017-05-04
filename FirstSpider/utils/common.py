import hashlib
import re


# 把url转化为md5
def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


# 从字符串中提取出数字
def extract_num(text):
    match_re = re.match(".*?(\d+).*", text)
    return int(match_re.group(1)) if match_re else 0

