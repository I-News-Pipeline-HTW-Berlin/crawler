import scrapy
from pymongo import MongoClient
from scrapy import Selector
from datetime import datetime
from ..items import ArticleItems
from ..settings import MONGO_URI,MONGO_DATABASE

root = 'https://taz.de'
testrun_cats = 3                     # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 10                     # limits the article links to crawl to this number. if zero, no limit.

class TazSpider(scrapy.Spider):
    name = "taz"
    start_url = root
    collection_name = 'scraped_articles'

    def start_requests(self):
        self.db_connect()
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        categories = response.xpath('//ul[@class="news navbar newsnavigation"]/li/a/@href').extract()
        categories = limit_crawl(categories,testrun_cats)
        for cat in categories:
            cat = add_host_to_url(cat)
            yield scrapy.Request(url=cat, callback=self.parse_categories)

    def parse_categories(self, response):
        def getLinkselector():
            # taz.de has different classes of links which direct to an article
            linkclasses = [
                "objlink report article",
                "objlink report article leaded pictured",
                "objlink brief report article leaded",
                "objlink brief report article pictured",
                "objlink subjective commentary article",
                "objlink brief subjective column article leaded"]

            linkselector = '//a[(@class=\"'
            linkselector_middle = '\") or (@class=\"'
            linkselector_end = '\")]/@href'
            for linkclass in linkclasses:
                linkselector+=linkclass + linkselector_middle
            linkselector = linkselector[:-len(linkselector_middle)] + linkselector_end
            return linkselector

        linklist = response.xpath(getLinkselector()).extract()
        linklist = limit_crawl(linklist,testrun_arts)
        for url in linklist:
            url = add_host_to_url(url)
            if not self.is_url_in_db(url):      # db-query
                yield scrapy.Request(url, callback=self.parse_articles)

    def parse_articles(self, response):

        def get_article_text():
            article_paragraphs = []
            html_article = response.xpath('//article/*').extract()      # every tag in <article>
            for tag in html_article:
                line = ""
                if "xmlns=\"\"" in tag or tag[2]=="6":  # only tags with 'xmlns="" (paragraphs) or h6-tags (subheadings)
                    tag_selector = Selector(text=tag)
                    html_line = tag_selector.xpath('//*/text()').extract()
                    for text in html_line:
                        line+=text
                    article_paragraphs.append(line)
            article_text = ""
            for paragraph in article_paragraphs:
                if paragraph:
                    article_text += paragraph + "\n\n"
            return article_text.strip()

        # if published_time is not set or wrong format, try modified, then None
        def get_pub_time():
            def parse_pub_time(time_str):
                try:
                    return datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S%z')  # "2019-11-14T10:50:00+01:00"
                except:
                    return None

            published_time_string = response.xpath('//meta[@property="article:published_time"]/@content').get()
            pub_time = parse_pub_time(published_time_string)
            if pub_time==None:
                modified_time_string = response.xpath('//meta[@property="article:modified_time"]/@content').get()
                pub_time = parse_pub_time(modified_time_string)
            return pub_time

        # Preparing for Output -> see items.py
        item = ArticleItems()

        item['crawl_time'] = datetime.now()
        item['long_url'] = response.xpath('//link[@rel=\"canonical\"]/@href').get()
        item['short_url'] = response.xpath('//meta[@property="og:url"]/@content').get()

        item['news_site'] = "taz.de"

        item['title'] = response.xpath('//meta[@property="og:title"]/@content').get()
        item['author'] = response.xpath('//meta[@name="author"]/@content').get()
        item['description'] = response.xpath('//meta[@name="description"]/@content').get()
        item['text'] = get_article_text()

        item['keywords'] = response.xpath('//meta[@name="keywords"]/@content').extract()
        item['published_time'] = get_pub_time()
        image_links = response.xpath('//meta[@property="og:image"]/@content').extract()
        item['image_links'] = add_host_to_url_list(image_links)
        links = response.xpath('//article /p[@xmlns=""]/a/@href').extract()
        item['links'] = add_host_to_url_list(links)
        item['_id'] = response.xpath('//link[@rel=\"canonical\"]/@href').get()

        yield item


    def db_connect(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DATABASE]

    def db_disconnect(self):
        self.client.close()

    def is_url_in_db(self, url):
        url_db = self.db[self.collection_name].find_one({"_id": url}, {"_id": 1})
        return url_db is not None


def add_host_to_url(url):
    if url and url[0] == '/':
        return root + url  # for relative paths it is necessary to add scheme and host
    return url

def add_host_to_url_list(url_list):
    complete_urls = []
    if(url_list):
        for url in url_list:
            complete_urls.append(add_host_to_url(url))
    return complete_urls

def limit_crawl(list,number):
    if list and number > 0 and number < len(list):
            return list[:number]

