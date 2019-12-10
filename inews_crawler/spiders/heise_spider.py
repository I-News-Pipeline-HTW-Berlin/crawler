import scrapy
from scrapy import Selector
import logging
from datetime import datetime
from ..items import ArticleItem
from ..utils import utils
import short_url

root = 'https://www.heise.de'
short_url_regex="\-[0-9]\d{1,10}"

testrun_cats = 0  # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 0  # limits the article links to crawl per category page to this number. if zero, no limit.

limit_category_pages = 0  # additional category pages of 50 articles each. Maximum of 400 pages
pages = 2 #number of pages to crawl it each category


# => 1. building the archive: 400
# => 2. daily use: 0 or 1
# don't forget to set the testrun variables to zero

class HeiseSpider(scrapy.Spider):
    name = "heise"
    start_url = root


    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        db = utils.db_connect(self)
        departments =response.css(".nav-category__list .nav-category__item a").xpath("@href").extract()
        departments = utils.limit_crawl(departments, testrun_cats)
        firstPage = True
        for department in departments:
            dep = department.split("/newsticker/")[-1].split("/")[0]
            department = root + department
            for i in range(2,pages+1):
                if(firstPage):
                    yield scrapy.Request(department,
                                 callback=self.parse_category,
                                 cb_kwargs=dict(department=dep, db=db))
                    firstPage=False
                else:
                    department = str(department) + "seite-" + str(i)+"/"
                    yield scrapy.Request(department,
                                             callback=self.parse_category,
                                             cb_kwargs=dict(department=dep, db=db))



    def parse_category(self, response, department, db):

        articles = response.css("#mitte article a ")
        links = articles.xpath("@href").extract()
        links = utils.limit_crawl(links,testrun_arts)

        for i in range(len(links)):
            links[i] =links[i][1:]
            url = utils.get_short_url(links[i],root,short_url_regex)
            links[i] = root+ "/"+links[i]
            if True:           # db-query
                description = articles[i].css(".a-article-teaser__synopsis::text").get()
                yield scrapy.Request(links[i], callback=self.parse_article,
                                     cb_kwargs=dict(description=description, url=links[i], dep=department))
            else:
                logging.debug("%s already in db", url)




    def parse_article(self, response, description, url, dep):

        # Article text: paragraphs and subheadings
        def get_article_text():
            art_parags=[]
            html_article = response.css(".article-content")
            tags = html_article.xpath('p|a|h3').extract()
            for tag in tags:
                lines=""
                sel = Selector(text=tag)
                html_lines =sel.xpath('//*/text()').extract()
                for line in html_lines:
                    lines+=line
                art_parags.append(lines)
            article_text = ""
            for paragraph in art_parags:
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

            item['news_site'] = "heise.de"
            item['title'] = response.css(".a-article-header__title::text").get().strip()
            item['authors'] =response.css(".a-creator__name::text").get().strip()

            item['description'] = description
            item['intro'] = description

            item['text'] = get_article_text()

            item['keywords'] = get_keywords()

            item['published_time'] = get_pub_time()
            item['image_links'] = response.xpath('//meta[@property="og:image"]/@content').extract()

            links =  response.css(".article-content a").xpath("@href").extract()
            item['links'] = utils.add_host_to_url_list(utils, links, root)
            item["l"]=l
            # don't save article without title or text
            if item['title'] and item['text']:
                yield item
            else:
                logging.debug("Cannot parse article: %s", url)
        else:
            logging.debug("Paywalled: %s", url)
