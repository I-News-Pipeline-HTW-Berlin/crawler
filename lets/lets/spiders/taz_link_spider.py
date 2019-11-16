import scrapy
from ..items import LinkItems

root = 'https://taz.de'
testrun = 3                     # limits the categories to crawl to this number. if zero, no limit.


class Taz_Links_Spider(scrapy.Spider):
    name = "taz_links"
    start_url = root
    collection_name = 'scraped_articles'
    INSERT_DB = False

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):
        categories = response.xpath('//ul[@class="news navbar newsnavigation"]/li/a/@href').extract()
        categories = self.limit_crawl(categories,testrun)
        for cat in categories:
            cat = self.add_host_to_url(cat)
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

        item = LinkItems()
        linklist = response.xpath(getLinkselector()).extract()
        item['url'] = self.add_host_to_url_list(linklist)
        yield item

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

    def limit_crawl(self,list,number):
        if number > 0 and number < len(list):
            return list[:number]