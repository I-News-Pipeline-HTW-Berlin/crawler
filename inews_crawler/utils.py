# Utils for spiders
from pymongo import MongoClient
from .settings import MONGO_URI, MONGO_DATABASE, COLLECTION_NAME
import re


collection_name = COLLECTION_NAME


class utils(object):

    # db

    def db_connect(self):
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        return db

    def is_url_in_db(url, db):
        url_db = db[collection_name].find_one({"short_url": url}, {"short_url": 1})
        return url_db is not None

    # url handling

    def add_host_to_url(url, root):
        if url and url[0] == '/':
            return root + url  # for relative paths it is necessary to add scheme and host
        return url

    def add_host_to_url_list(self, url_list,root):
        complete_urls = []
        if(url_list):
            for url in url_list:
                complete_urls.append(self.add_host_to_url(url, root))
        return complete_urls

    def get_short_url(url, root, regex):
        return root + '/' + re.search(regex, url).group()


    # item handling

    def not_none_string(s):
        result = ""
        if s != None:
            result = s
        return result

    def not_none_list(l):
        result = []
        if l != None:
            result = l
        return result



    # limit spider

    def limit_crawl(list,number):
        if list and number > 0 and number < len(list):
                return list[:number]
        else:
            return list
