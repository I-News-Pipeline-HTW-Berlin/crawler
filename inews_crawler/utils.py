# Utils for spiders
from datetime import datetime
import logging
from pymongo import MongoClient
from .settings import MONGO_URI, MONGO_DATABASE, ARTICLE_COLLECTION_NAME, LOG_COLLECTION_NAME
import re
from .items import LogItem



article_collection_name = ARTICLE_COLLECTION_NAME
log_collection_name = LOG_COLLECTION_NAME

# opens DB-Connection
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]


class utils(object):

    # db

    def is_url_in_db(url):
        url_db = db[article_collection_name].find_one({"short_url": url}, {"short_url": 1})
        return url_db is not None

    def log_event(self, news_site, url, property_name, level):
        log_item = LogItem()
        log_item['news_site'] = news_site
        log_item['log_time'] = datetime.now()
        log_item['url'] = url
        log_item['property'] = property_name
        log_item['level'] = level
        db[log_collection_name].insert(dict(log_item))


    # url handling

    def add_host_to_url(self, url, root):
        if url is not None and len(url) > 0 and str(url)[0] == '/':
            return root + url  # for relative paths it is necessary to add scheme and host
        return url

    def add_host_to_url_list(self, url_list, root):
        complete_urls = []
        if url_list is not None and len(url_list) > 0:
            for url in url_list:
                complete_urls.append(self.add_host_to_url(url, root))
        return complete_urls

    def get_short_url(url, root, regex):
        if url is not None:
            regex = re.search(regex, url)
            if regex is not None:
                return root + '/' + regex.group()
        return url


    # item handling

    def not_none_string(s):
        result = ""
        if s is not None:
            result = s
        return result

    def not_none_list(l):
        result = []
        if l is not None:
            result = l
        return result



    # limit spider

    def limit_crawl(list,number):
        if list is not None and number > 0 and number < len(list):
                return list[:number]
        else:
            return list



    # get_items with css and xpath option + multiple expressions
    # - including logging warnings
    # - avoiding None-objects

    # get simple string of item property
    def get_item_string(self, response, property_name, url, sel, expr_list, news_site):
        for expr in expr_list:
            if sel=="css":
                property = response.css(expr).get()
            elif sel=="xpath":
                property = response.xpath(expr).get()
            else:
                property = ""
            if property is not None and len(property.strip()) > 0:
                return property.strip()
        self.log_event(news_site, url, property_name, 'warning')
        logging.warning("Cannot parse %s: %s", property_name, url)
        return ""

    # get list of item property
    def get_item_list(self, response, property_name, url, sel, expr_list, news_site):
        for expr in expr_list:
            if sel=="css":
                property = response.css(expr).extract()
            elif sel=="xpath":
                property = response.xpath(expr).extract()
            else:
                property = []
            if property is not None:
                return list(set(property))
        self.log_event(news_site, url, property_name, 'warning')
        logging.warning("Cannot parse %s: %s", property_name, url)
        return []

    # get list of item property by splitting string
    def get_item_list_from_str(self, response, property_name, url, sel, expr_list, split_str, news_site):
        for expr in expr_list:
            if sel=="css":
                property = response.css(expr).get()
            elif sel=="xpath":
                property = response.xpath(expr).get()
            else:
                property = ""
            if property is not None:
                return property.split(split_str)
        self.log_event(news_site, url, property_name, 'warning')
        logging.warning("Cannot parse %s: %s", property_name, url)
        return []
