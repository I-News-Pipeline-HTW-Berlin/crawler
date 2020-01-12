import scrapy
from scrapy import Selector
from datetime import datetime
import logging
from ..items import ArticleItem
from ..utils import utils

root = 'https://sueddeutsche.de'
short_url_regex = "\d(\.|\d)+$" # https://sueddeutsche.de/1.3456789
full_article_addition = '-0'    # if article extends over multiple pages this url addition will get the full article

testrun_cats = 0                # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 0                # limits the article links to crawl per category page to this number. if zero, no limit.

limit_pages = 1                 # additional category pages of 50 articles each. Maximum of 400 pages
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
            short_url = utils.get_short_url(links[i],root, short_url_regex)
            if short_url and not utils.is_url_in_db(short_url, db):           # db-query
                description = articles[i].css(".sz-teaser__summary::text").get()
                yield scrapy.Request(links[i]+full_article_addition, callback=self.parse_article,
                                     cb_kwargs=dict(description=description, long_url=links[i], short_url=short_url,
                                                    dep=department))
            else:
                logging.info("%s already in db", short_url)

        offSet = 0
        more = "https://www.sueddeutsche.de/overviewpage/additionalDepartmentTeasers?departmentId={}&offset={}&size=50&isMobile=false".format(
            departmentIds[department], offSet)

        while offSet/25 < limit_pages:  # max 1000
            yield scrapy.Request(more, callback=self.parse_category, cb_kwargs=dict(department=department, db=db))
            offSet = offSet + 25
            more = "https://www.sueddeutsche.de/overviewpage/additionalDepartmentTeasers?departmentId={}&offset={}&size=50&isMobile=false".format(
                departmentIds[department], offSet)

    def parse_article(self, response, description, short_url, long_url, dep):
        utils_obj = utils()

        # Intro: bullet points or continuous text
        def get_intro():
            article_Intro = response.css(".sz-article-intro__wysiwyg ul li::text").extract()
            if article_Intro:
                intro = ""
                for int in article_Intro:
                    intro = intro + int
            else:
                intro = response.css(".sz-article-intro__abstract-text::text").get()
            if not intro:
                logging.warning("Cannot parse intro: %s", short_url)
                intro = ""
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
            text = article_text.strip()
            if not text:
                logging.warning("Cannot parse article text: %s", short_url)
            return text

        def get_pub_time():
            time_str = response.xpath('//time/@datetime').get()
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')  # "2019-11-21 21:53:09"
            except:
                logging.warning("Cannot parse published time: %s", short_url)
                return None


        # don't save paywalled article-parts
        paywall = response.xpath('//offer-page').get()
        if not paywall:

            item = ArticleItem()

            item['crawl_time'] = datetime.now()
            item['long_url'] = long_url
            item['short_url'] = short_url

            item['news_site'] = "sz"
            item['title'] = utils.get_item_string(utils_obj, response, 'title', short_url, 'xpath',
                                                  ['//meta[@property="og:title"]/@content'])
            item['authors'] = utils.get_item_list(utils_obj, response, 'authors', short_url, 'xpath',
                                                    ['//meta[@name="author"]/@content'])

            item['description'] = description
            item['intro'] = get_intro()
            item['text'] = get_article_text()

            keywords = utils.get_item_list_from_str(utils_obj, response, 'keywords', short_url, 'xpath',
                                                            ['//meta[@name="keywords"]/@content'],',')
            item['keywords'] = list(set(keywords) - set(["Süddeutsche Zeitung"]))

            item['published_time'] = get_pub_time()
            item['image_links'] = utils.get_item_list(utils_obj, response, 'image_links', short_url, 'xpath',
                                                               ['//meta[@property="og:image"]/@content'])

            links =  utils.get_item_list(utils_obj, response, 'links', short_url, 'xpath',
                                         ['//div[@class="sz-article__body sz-article-body"]/p/a/@href'])
            item['links'] = utils.add_host_to_url_list(utils_obj, links, root)

            # don't save article without title or text
            if item['title'] and item['text']:
                    yield item
            else:
                logging.info("Cannot parse article: %s", short_url)
        else:
            logging.info("Paywalled: %s", short_url)
