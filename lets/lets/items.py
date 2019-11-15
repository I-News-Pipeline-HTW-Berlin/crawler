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
    crawl_time = scrapy.Field()     # datetime.now()
    long_url = scrapy.Field()       # String
    short_url = scrapy.Field()      # String

    news_site = scrapy.Field()      # String: taz.de, sueddeutsche.de
    title = scrapy.Field()          # String
    author = scrapy.Field()         # String
    description = scrapy.Field()    # String
    text = scrapy.Field()           # String

    keywords = scrapy.Field()       # List(String)
    published_time = scrapy.Field() # datetime
    image_links = scrapy.Field()    # List(String)
    links = scrapy.Field()          # List(String)
    _id = scrapy.Field()            # String




