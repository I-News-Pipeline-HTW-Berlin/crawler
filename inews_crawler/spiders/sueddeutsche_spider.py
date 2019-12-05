import scrapy
from scrapy import Selector
from datetime import datetime
import logging
from ..items import ArticleItem
from ..utils import utils

root = 'https://sueddeutsche.de'
short_url_regex = "\d(\.|\d)+$" # https://sueddeutsche.de/1.3456789

testrun_cats = 3                # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 0                # limits the article links to crawl per category page to this number. if zero, no limit.

limit_category_pages = 0        # additional category pages of 50 articles each. Maximum of 400 pages
                                # => 1. building the archive: 400
                                # => 2. daily use: 0 or 1
                                # don't forget to set the testrun variables to zero


class SueddeutscheSpider(scrapy.Spider):
    name = "sueddeutsche"
    start_urls = [root]



    def parse(self, response):
        db = utils.db_connect(self)
        departments = response.css("#header-departments .nav-item-link").xpath("@href").extract()
        departments = utils.limit_crawl(departments,testrun_cats)

        for department in departments:
            dep = department.split("/")[-1]
            yield scrapy.Request(department,
                                 callback=self.parse_category,
                                 cb_kwargs=dict(department=dep, db=db))


    def parse_category(self, response, department, db):

        departmentIds = {
            "politik": "sz.2.236",
            "wirtschaft": "sz.2.222",
            "meinung": "sz.2.238",
            "panorama": "sz.2.227",
            "sport": "sz.2.235",
            "muenchen": "sz.2.223",
            "bayern": "sz.2.226",
            "kultur": "sz.2.237",
            "leben": "sz.2.225",
            "wissen": "sz.2.240",
            "digital": "sz.2.233",
            "karriere": "sz.2.234",
            "reise": "sz.2.241",
            "auto": "sz.2.232"
        }

        articles = response.css(".sz-teaser")
        links = articles.xpath("@href").extract()
        links = utils.limit_crawl(links,testrun_arts)


        for i in range(len(links)):
            url = utils.get_short_url(links[i],root, short_url_regex)
            ##############################################################
            # print(str(i) + ": " + department + ": ToCheckandScrape: " + links[i])
            if not utils.is_url_in_db(url, db):           # db-query
                description = articles[i].css(".sz-teaser__summary::text").get()
                yield scrapy.Request(links[i], callback=self.parse_article,
                                     cb_kwargs=dict(description=description, url=links[i], dep=department))
            else:
                logging.debug("%s already in db", url)

        offSet = 0
        more = "https://www.sueddeutsche.de/overviewpage/additionalDepartmentTeasers?departmentId={}&offset={}&size=50&isMobile=false".format(
            departmentIds[department], offSet)

        while offSet/25 < limit_category_pages:  # max 1000
            yield scrapy.Request(more, callback=self.parse_category, cb_kwargs=dict(department=department, db=db))
            offSet = offSet + 25
            more = "https://www.sueddeutsche.de/overviewpage/additionalDepartmentTeasers?departmentId={}&offset={}&size=50&isMobile=false".format(
                departmentIds[department], offSet)



    def parse_article(self, response, description, url, dep):

        # Intro: bullet points or continuous text
        def get_intro():
            article_Intro = response.css(".sz-article-intro__wysiwyg ul li::text").extract()
            if article_Intro:
                intro = ""
                for int in article_Intro:
                    intro = intro + int
            else:
                intro = response.css(".sz-article-intro__abstract-text::text").get()
            return intro

        # Article text: paragraphs and subheadings
        def get_article_text():
            article_paragraphs = []
            html_article = response.xpath('//div[@class="sz-article__body sz-article-body"]')
            article_tags = html_article.xpath('p|h3').extract()
            for tag in article_tags:
                line = ""
                tag_selector = Selector(text=tag)
                html_line = tag_selector.xpath('//*/text()').extract()
                for text in html_line:
                    line += text
                article_paragraphs.append(line)
            article_text = ""
            for paragraph in article_paragraphs:
                if paragraph:
                    article_text += paragraph + "\n\n"
            return article_text.strip()

        def get_pub_time():
            time_str = response.xpath('//time/@datetime').get()
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')  # "2019-11-21 21:53:09"
            except:
                return None

        # converts keywords string to list of keywords
        def get_keywords():
            keywords_str = response.xpath('//meta[@name="keywords"]/@content').get()
            return keywords_str.split(",")

        # don't save paywalled article-parts
        paywall = response.xpath('//offer-page').get()
        if not paywall:

            item = ArticleItem()

            item['crawl_time'] = datetime.now()
            item['long_url'] = url
            item['short_url'] = utils.not_none_string(utils.get_short_url(url, root, short_url_regex))

            item['news_site'] = "sueddeutsche.de"
            item['title'] = response.xpath('//meta[@property="og:title"]/@content').get()
            item['authors'] = response.xpath('//meta[@name="author"]/@content').extract()
                # response.xpath('//article/p[@class="sz-article__byline sz-article-byline"]/a/text()').extract()


            item['description'] = description
            item['intro'] = get_intro()
            item['text'] = get_article_text()

            item['keywords'] = get_keywords()

            item['published_time'] = get_pub_time()
            item['image_links'] = response.xpath('//meta[@property="og:image"]/@content').extract()

            links = response.xpath('//div[@class="sz-article__body sz-article-body"]/p/a/@href').extract()
            item['links'] = utils.add_host_to_url_list(utils, links, root)

            # don't save article without title or text
            if item['title'] and item['text']:
                    yield item
            else:
                logging.debug("Cannot parse article: %s", url)
        else:
            logging.debug("Paywalled: %s", url)
