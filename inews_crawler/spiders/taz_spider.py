import scrapy
from scrapy import Selector
import logging
from datetime import datetime
from ..items import ArticleItem
from ..utils import utils

root = 'https://taz.de'
short_url_regex = "!\d{5,}"         # https://taz.de/!2345678/

testrun_cats = 2                    # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 3                    # limits the article links to crawl to this number. if zero, no limit.
                                    # For deployment: don't forget to set the testrun variables to zero

class TazSpider(scrapy.Spider):
    name = "taz"
    start_url = root

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        db = utils.db_connect(self)
        print(db)
        categories = response.xpath('//ul[@class="news navbar newsnavigation"]/li/a/@href').extract()
        categories = utils.limit_crawl(categories,testrun_cats)
        for cat in categories:
            cat = utils.add_host_to_url(cat,root)
            yield scrapy.Request(url=cat, callback=self.parse_category, cb_kwargs=dict(db=db))

    def parse_category(self, response, db):
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
        linklist = utils.limit_crawl(linklist,testrun_arts)
        if linklist:
            for url in linklist:
                url = utils.get_short_url(url, root, short_url_regex)
                if not utils.is_url_in_db(url, db):      # db-query
                    yield scrapy.Request(url, callback=self.parse_article, cb_kwargs=dict(url=url))
                else:
                    logging.debug("%s already in db", url)


    def parse_article(self, response, url):

        def get_article_text():
            article_paragraphs = []
            html_article = response.xpath('//article/*').extract()      # every tag in <article>
            for tag in html_article:
                line = ""
                # only p tags with 'xmlns="" and class beginning with "article..." (paragraphs) or h6-tags (subheadings)
                if "p xmlns=\"\" class=\"article" in tag or tag[2]=="6":
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

        # converts keywords string to list of keywords
        def get_keywords():
            keywords_str = response.xpath('//meta[@name="keywords"]/@content').get()
            keywords = keywords_str.strip().split(", ")
            if "taz" in keywords:
                keywords.remove("taz")
            if "tageszeitung" in keywords:
                keywords.remove("tageszeitung")
            return keywords

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
        item = ArticleItem()

        item['crawl_time'] = datetime.now()
        item['long_url'] = response.xpath('//link[@rel=\"canonical\"]/@href').get()
        # short_url = response.xpath('//meta[@property="og:url"]/@content').get()
        item['short_url'] = url

        item['news_site'] = "taz"
        item['title'] = response.xpath('//meta[@property="og:title"]/@content').get()
        item['authors'] = response.xpath('//meta[@name="author"]/@content').extract()
        item['description'] = response.xpath('//meta[@name="description"]/@content').get()
        item['intro'] = response.xpath('//article/p[@class="intro "]/text()').get()
        item['text'] = get_article_text()

        item['keywords'] = get_keywords()
        item['published_time'] = get_pub_time()
        image_links = response.xpath('//meta[@property="og:image"]/@content').extract()
        item['image_links'] = utils.add_host_to_url_list(utils, image_links, root)
        links = response.xpath('//article /p[@xmlns=""]/a/@href').extract()
        item['links'] = utils.add_host_to_url_list(utils, links, root)

        # don't save article without title or text
        if item['title'] and item['text']:
            yield item
        else:
            logging.debug("Cannot parse article: %s", url)
        yield item
