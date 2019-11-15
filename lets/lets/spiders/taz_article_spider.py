import scrapy
from scrapy.loader import ItemLoader
from scrapy import Selector
from ..items import ArticleItems
import json
from datetime import datetime

root = 'https://taz.de'
testrun = 10                     # limits the links to crawl to this number. if zero, no limit.

class TazSpider(scrapy.Spider):
    name = "taz_articles"
    start_url = root

    # opens crawled json with article links, removes duplicates and converts to list
    def prepare_links(self):
        linkset = set()
        with open("taz_links.json", encoding='utf-8', errors='ignore') as json_data:
            links = json.load(json_data, strict=False)
        for page in links:
            if(page):
                for url in page["url"]:
                    if url[0] == '/':
                        url = root + url        # for relational paths its necessary to add scheme and host
                    linkset.add(url)
        return list(linkset)

    def start_requests(self):
        start_urls = self.prepare_links()
        if testrun>0 and testrun<len(start_urls):
            start_urls = start_urls[:testrun]
        for url in start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):

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


        # Preparing for Output -> see items.py
        l = ItemLoader(item=ArticleItems(), response=response)

        l.add_value('crawl_time',datetime.now())
        l.add_xpath('long_url', '//link[@rel=\"canonical\"]/@href')
        l.add_xpath('short_url', '//meta[@property="og:url"]/@content')

        l.add_value('news_site',"taz.de")
        l.add_xpath('title', '//meta[@property="og:title"]/@content')
        l.add_xpath('author', '//meta[@name="author"]/@content')
        l.add_xpath('description', '//meta[@name="description"]/@content')
        l.add_value('text', get_article_text())

        l.add_xpath('keywords', '//meta[@name="keywords"]/@content')
        l.add_xpath('published_time', '//meta[@property="article:published_time"]/@content')
        l.add_xpath('image_links', '//meta[@property="og:image"]/@content')
        l.add_xpath('links', '//article /p[@xmlns=""]/a/@href')

        return l.load_item()
