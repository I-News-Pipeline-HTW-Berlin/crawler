# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import logging
from datetime import datetime

import pymongo

from .utils import utils
from inews_crawler.items import ArticleItem, LogItem
from .settings import ARTICLE_COLLECTION_NAME, LOG_COLLECTION_NAME

class MongoPipeline(object):

    article_collection_name = ARTICLE_COLLECTION_NAME
    log_collection_name = LOG_COLLECTION_NAME

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        ## pull in information from settings.py
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        ## initializing spider
        ## opening db connection
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        ## clean up when spider is closed
        self.client.close()

    def process_item(self, item, spider):
        log_item = LogItem()
        collection_name = self.article_collection_name
        ## how to handle each post
        self.db[collection_name].ensure_index("short_url", unique=True)
        try:
            self.db[collection_name].insert(dict(item))
        except:
            logging.info("Duplicate not added to MongoDB: %s", item['short_url'])
            utils.log_event(utils(), item['news_site'], item['short_url'], 'duplicate', 'info')
        else:
            logging.info("Post added to MongoDB: %s", item['short_url'])
            utils.log_event(utils(), item['news_site'], item['short_url'], 'added', 'info')
        return item
