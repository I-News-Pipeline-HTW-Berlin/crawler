import scrapy
from scrapy import Selector
from ..items import ArticleItems
import json
from datetime import datetime

root = 'https://taz.de'
testrun = 10                     # limits the links to crawl to this number. if zero, no limit.

class TazSpider(scrapy.Spider):
    name = "taz_articles"
    start_url = root
    INSERT_DB = True

    # opens crawled json with article links, removes duplicates and converts to list
    def prepare_links(self):
        linkset = set()
        with open("taz_links.json", encoding='utf-8', errors='ignore') as json_data:
            links = json.load(json_data, strict=False)
        for category in links:
            if(category):
                for url in category["url"]:
                    linkset.add(url)
        return list(linkset)

    def start_requests(self):
        start_urls = self.prepare_links()
        start_urls = self.limit_crawl(start_urls,testrun)
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
        published_time_string = response.xpath('//meta[@property="article:published_time"]/@content').get()
        pub_time = datetime.strptime(published_time_string,'%Y-%m-%dT%H:%M:%S%z')       # "2019-11-14T10:50:00+01:00"
        item['published_time'] = pub_time
        image_links = response.xpath('//meta[@property="og:image"]/@content').extract()
        item['image_links'] = self.add_host_to_url_list(image_links)
        links = response.xpath('//article /p[@xmlns=""]/a/@href').extract()
        item['links'] = self.add_host_to_url_list(links)
        item['_id'] = response.xpath('//link[@rel=\"canonical\"]/@href').get()

        yield item

    def limit_crawl(self, list, number):
        if number > 0 and number < len(list):
            return list[:number]

    def add_host_to_url(self,url):
        if url[0] == '/':
            url = root + url  # for relative paths it is necessary to add scheme and host
        return url

    def add_host_to_url_list(self, url_list):
        complete_urls = []
        if url_list:
            for url in url_list:
                complete_urls.append(self.add_host_to_url(url))
        return complete_urls