# Utils for spiders
from pymongo import MongoClient
from .settings import MONGO_URI,MONGO_DATABASE, COLLECTION_NAME

collection_name = COLLECTION_NAME

# db

def db_connect(self):
    self.client = MongoClient(MONGO_URI)
    self.db = self.client[MONGO_DATABASE]

def is_url_in_db(self, url):
    url_db = self.db[collection_name].find_one({"_id": url}, {"_id": 1})
    return url_db is not None


# url handling

def add_host_to_url(url, root):
    if url and url[0] == '/':
        return root + url  # for relative paths it is necessary to add scheme and host
    return url

def add_host_to_url_list(url_list,root):
    complete_urls = []
    if(url_list):
        for url in url_list:
            complete_urls.append(add_host_to_url(url,root))
    return complete_urls

def get_short_url(url, root, length):
    return root + '/' + url[-length:]


# limit spider

def limit_crawl(list,number):
    if list and number > 0 and number < len(list):
            return list[:number]
    else:
        return list
