# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LetsItem(scrapy.Item):
    # define the fields for your item here like:

    department = scrapy.Field()

    title = scrapy.Field()
    article = scrapy.Field()
    intro = scrapy.Field()
    author = scrapy.Field()
    summery = scrapy.Field()
    url = scrapy.Field()
    published = scrapy.Field()


