# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ArticleItem(scrapy.Item):
    crawl_time = scrapy.Field()     # datetime.now()
    short_url = scrapy.Field()      # String SHORT_URL 'https://taz.de/!5642421/'
    long_url = scrapy.Field()       # String 'https://taz.de/Machtkampf-in-Bolivien/!5642421/'

    news_site = scrapy.Field()      # String: taz.de, sueddeutsche.de
    title = scrapy.Field()          # String
    authors = scrapy.Field()        # List(String)
    description = scrapy.Field()    # String: Teaser for article, sometimes same as lead/intro
    intro = scrapy.Field ()         # String: Lead/intro, sometimes same as description/teaser
    text = scrapy.Field()           # String

    keywords = scrapy.Field()       # List(String)
    published_time = scrapy.Field() # datetime or None
    image_links = scrapy.Field()    # List(String)
    links = scrapy.Field()          # List(String)





