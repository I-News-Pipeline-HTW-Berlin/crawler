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


class LinkItems(scrapy.Item):
    url = scrapy.Field()


class ArticleItems(scrapy.Item):
    crawl_time = scrapy.Field()
    long_url = scrapy.Field()
    short_url = scrapy.Field()

    news_site = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    description = scrapy.Field()
    text = scrapy.Field()

    keywords = scrapy.Field()
    published_time = scrapy.Field()
    image_links = scrapy.Field()
    links = scrapy.Field()



