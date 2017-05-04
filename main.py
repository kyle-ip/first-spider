# -*- coding: utf-8 -*-

from scrapy.cmdline import execute

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
execute(["scrapy", "crawl", "zhihu"])


