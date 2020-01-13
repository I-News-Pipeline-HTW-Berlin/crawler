import scrapy
from scrapy import Selector
import logging
from datetime import datetime
from ..items import ArticleItem
from ..utils import utils

root = 'https://www.heise.de'
short_url_regex="\-[0-9]\d{6,}"
full_article_addition = '?seite=all'  # if article extends over multiple pages this url addition will get the full article

testrun_cats = 0    # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 0    # limits the article links to crawl per category page to this number. if zero, no limit.

limit_pages = 1     # => 1. building the archive: 0
                    # => 2. daily use: 3 or 4
                    # don't forget to set the testrun variables to zero

class HeiseSpider(scrapy.Spider):
    name = "heise"
    start_url = root
    utils_obj = utils()


    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        db = utils.db_connect(self)
        departments =response.css(".nav-category__list .nav-category__item a").xpath("@href").extract()
        departments = utils.limit_crawl(departments, testrun_cats)
        for department_url in departments:
            department_url = root + department_url
            yield scrapy.Request(department_url,
                                 callback=self.parse_category,
                                 cb_kwargs=dict(db=db, department_url=department_url, page=1, limit_pages=limit_pages))


    def parse_category(self, response, db, department_url, page, limit_pages):
        utils_obj = utils()
        def find_last_page():
            links = response.xpath('//li/a/@href').extract()
            pagination = []
            for link in links:
                if "/seite-" in link:
                    pagination.append((int)(link.split("-")[-1][:-1]))
            return max(pagination)

        if not limit_pages:
            limit_pages = find_last_page()

        if page<limit_pages:
            dep_page = department_url + "seite-" + str(page + 1) + "/"
            yield scrapy.Request(dep_page,
                                 callback=self.parse_category,
                                 cb_kwargs=dict(db=db, department_url=department_url, page=page + 1,
                                                limit_pages=limit_pages))


        department_name = utils.get_item_string(utils_obj, response, 'department', department_url, 'xpath',
                                                ['//meta[@name="title"]/@content'])
        articles = response.xpath('//section[@class="article-teaser__list"]/article').extract()
        limited_articles = utils.limit_crawl(articles,testrun_arts)

        for article in limited_articles:
            article_html = Selector(text=article)
            long_url = article_html.xpath('//a/@href').get()
            long_url = utils.add_host_to_url(utils_obj, long_url, root)
            short_url = utils.not_none_string(utils.get_short_url(long_url, root, short_url_regex))
            # Filter techstage articles
            if not "techstage.de" in long_url:
                # Filter paywalled articles
                if not "heiseplus" in article:
                    if short_url and not utils.is_url_in_db(short_url, db):  # db-query
                        description = utils.get_item_string(utils_obj, article_html, 'description', department_url, 'xpath',
                                                            ['//p[@class="a-article-teaser__synopsis "]/text()'])
                        yield scrapy.Request(long_url+full_article_addition, callback=self.parse_article,
                                             cb_kwargs=dict(description=description, long_url=long_url,
                                                            short_url=short_url, department_name=department_name))
                    else:
                        logging.info("%s already in db", short_url)
                else:
                    logging.info("%s is paywalled", short_url)


    def parse_article(self, response, description, long_url, short_url, department_name):
        utils_obj = utils()

        # Article text: paragraphs and subheadings
        def get_article_text():
            art_parags=[]
            html_article = response.css(".article-content")
            if not html_article:
                html_article = response.css(".article_page_text")

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
            text = article_text.strip()
            if not text:
                logging.warning("Cannot parse article text: %s", short_url)
            return text


        # Filter links
        def get_links():
            links = utils.get_item_list(utils_obj,response,'links',short_url,'css',
                                        ['.article_page_text a::attr(href)',
                                         '.article-content a::attr(href)'])
            if links:
                filtered_links = set()
                for link in links:
                    if not link=="/" and not link[:6] == "/forum" and not link[:6] == "mailto" and not "geizhals" in link:
                        filtered_links.add(link)
                return utils.add_host_to_url_list(utils_obj, list(filtered_links), root)
            else:
                return []

        def get_pub_time():
            time_str = response.xpath('//time/@datetime').get()
            try:
                return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')  # "2020-01-03T07:13:00"
            except:
                try:
                    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S%z')  # "2020-01-03T07:13:00+01:00"
                except:
                    logging.warning("Cannot parse published time: %s", short_url)
                    return None


        # don't save paywalled articles (not necessary because paywalled articles are filtered in parse_category)
        def is_paywalled():
            print(response.xpath('//a-paid-content-teaser/@class').get())
            print(response.xpath('//div/@id').extract())
            paywall_heise = response.xpath('//a-paid-content-teaser/@class').get() != None
            paywall_ct = "purchase" in response.xpath('//div/@id').extract()
            return paywall_heise & paywall_ct


        item = ArticleItem()

        item['crawl_time'] = datetime.now()
        item['long_url'] = long_url
        item['short_url'] = short_url

        item['news_site'] = "heise"
        item['title'] = utils.get_item_string(utils_obj,response,'title',short_url,'xpath',
                                              ['//meta[@property="og:title"]/@content',
                                               '//meta[@name="title"]/@content'])
        item['authors'] = utils.get_item_list(utils_obj,response,'authors',short_url,'xpath',
                                              ['//meta[@name="author"]/@content'])
        item['description'] = description
        item['intro'] = utils.get_item_string(utils_obj,response,'intro',short_url,'css',
                                              ['p.a-article-header__lead::text',
                                               'p.article_page_intro strong::text'])

        item['text'] = get_article_text()

        keywords = utils.get_item_list_from_str(utils_obj, response,'keywords',short_url,'xpath',
                                                        ['//meta[@name="keywords"]/@content'],", ")
        # add department name to keywords for UIMA mapping
        if department_name:
            keywords.append(department_name)
        item['keywords'] = keywords

        item['published_time'] = get_pub_time()
        item['image_links'] = utils.get_item_list(utils_obj,response,'image_links',short_url,'xpath',
                                                  ['//meta[@property="og:image"]/@content'])

        item['links'] = get_links()

        # don't save article without title or text
        if item['title'] and item['text']:
            yield item
        else:
            logging.info("Cannot parse article: %s", short_url)