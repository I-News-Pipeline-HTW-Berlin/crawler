import scrapy
from scrapy import Selector
import logging
from datetime import datetime
from ..items import ArticleItem
from ..utils import utils

root = 'https://taz.de'
short_url_regex = "!\d{5,}"         # helps converting long to short url: https://taz.de/!2345678/

testrun_cats = 0                    # limits the categories to crawl to this number. if zero, no limit.
testrun_arts = 0                    # limits the article links to crawl to this number. if zero, no limit.
                                    # For deployment: don't forget to set the testrun variables to zero

class TazSpider(scrapy.Spider):
    name = "taz"
    start_url = root

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    # scrape main page for categories
    def parse(self, response):
        categories = response.xpath('//ul[@class="news navbar newsnavigation"]/li/a/@href').extract()
        categories = utils.limit_crawl(categories,testrun_cats)
        for cat in categories:
            cat = utils.add_host_to_url(self, cat, root)
            yield scrapy.Request(url=cat, callback=self.parse_category)

    # scrape category pages for articles
    def parse_category(self, response):

        # taz.de has different classes of links which direct to an article
        def getLinkselector():
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
            for long_url in linklist:
                short_url = utils.get_short_url(long_url, root, short_url_regex)
                if short_url and not utils.is_url_in_db(short_url):  # db-query
                    yield scrapy.Request(short_url+"/", callback=self.parse_article,
                                         cb_kwargs=dict(short_url=short_url, long_url=long_url))
                else:
                    utils.log_event(utils(), self.name, short_url, 'exists', 'info')
                    logging.info('%s already in db', short_url)


    def parse_article(self, response, short_url, long_url):
        utils_obj = utils()

        def get_article_text():
            article_paragraphs = []
            html_article = response.xpath('//article/*').extract()      # every tag in <article>
            for tag in html_article:
                line = ""
                # only p tags with 'xmlns="" and class beginning with "article..." (=paragraphs)
                # or h6-tags (=subheadings)
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
            text = article_text.strip()
            if not text:
                utils.log_event(utils_obj, self.name, short_url, 'text', 'warning')
                logging.warning("Cannot parse article text: %s", short_url)
            return text


        # if published_time is not set or wrong format, try modified, then None
        def get_pub_time():
            def parse_pub_time(time_str):
                try:
                    return datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S%z')  # "2019-11-14T10:50:00+01:00"
                except:
                    time_str = time_str[:-6]
                    try:
                        return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')  # "2019-11-14T10:50:00"
                    except:
                        return None

            published_time_string = response.xpath('//meta[@property="article:published_time"]/@content').get()
            modified_time_string = response.xpath('//meta[@property="article:modified_time"]/@content').get()
            pub_time = parse_pub_time(published_time_string)
            mod_time = parse_pub_time(modified_time_string)
            if pub_time is not None:
                return pub_time
            elif mod_time is not None:
                return mod_time
            else:
                utils.log_event(utils_obj, self.name, short_url, 'published_time', 'warning')
                logging.warning("Cannot parse published time: %s", short_url)
                return None



        # Preparing for Output -> see items.py
        item = ArticleItem()

        item['crawl_time'] = datetime.now()
        item['long_url'] = utils.add_host_to_url(utils_obj, long_url, root)
        item['short_url'] = short_url

        item['news_site'] = "taz"
        item['title'] = utils.get_item_string(utils_obj, response, 'title', short_url, 'xpath',
                                              ['//meta[@property="og:title"]/@content'], self.name)
        item['authors'] = utils.get_item_list(utils_obj, response, 'authors', short_url, 'xpath',
                                              ['//meta[@name="author"]/@content'], self.name)
        item['description'] = utils.get_item_string(utils_obj, response, 'description', short_url, 'xpath',
                                                    ['//meta[@name="description"]/@content'], self.name)
        item['intro'] = utils.get_item_string(utils_obj, response, 'intro', short_url, 'xpath',
                                              ['//article/p[@class="intro "]/text()'], self.name)
        item['text'] = get_article_text()

        keywords = utils.get_item_list_from_str(utils_obj, response, 'keywords', short_url, 'xpath',
                                                ['//meta[@name="keywords"]/@content'],', ', self.name)
        item['keywords'] = list(set(keywords) - {"taz", "tageszeitung "})
        item['published_time'] = get_pub_time()

        image_links = utils.get_item_list(utils_obj, response, 'image_links', short_url, 'xpath',
                                          ['//meta[@property="og:image"]/@content'], self.name)
        item['image_links'] = utils.add_host_to_url_list(utils_obj, image_links, root)

        links = utils.get_item_list(utils_obj, response, 'links', short_url, 'xpath',
                                    ['//article /p[@xmlns=""]/a/@href'], self.name)
        item['links'] = utils.add_host_to_url_list(utils_obj, links, root)

        # don't save article without title or text
        if item['title'] and item['text']:
            yield item
        else:
            logging.info("Cannot parse article: %s", short_url)
            utils.log_event(utils_obj, self.name, short_url, 'missingImportantProperty', 'info')

