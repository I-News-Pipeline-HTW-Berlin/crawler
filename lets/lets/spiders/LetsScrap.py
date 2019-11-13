import time

import scrapy
from ..items import LetsItem


class LetsScrap(scrapy.Spider):
    name = "lets"
    start_urls = ['https://www.sueddeutsche.de/']



    def parse(self, response):

        departments = response.css("#header-departments .nav-item-link").xpath("@href").extract()

        for department in departments:
            items = LetsItem()
            dep = department.split("/")[-1]
            yield scrapy.Request(department,
                                 callback=self.scanDepartment,
                                 cb_kwargs=dict(items=items, department=dep))



    def getArticle(self, response, items, summery, url, dep):
        title = response.css(".sz-article-header__title::text").get()
        article_Intro = response.css(".sz-article-intro__wysiwyg ul li::text").extract()
        intro = ""

        for int in article_Intro:
            intro = intro + int
        if len(intro) <= 0:
            intro = response.css(".sz-article-intro__abstract-text::text").get()

        article = response.css(".sz-article-body > p")
        linksInArticle = response.css(".sz-article-body > p > a").extract()
        linksTexts = response.css(".sz-article-body > p > a::text").extract()
        replacedArticle = ""
        if len(linksInArticle) > 0:

            temp = ""
            for p in article:
                tempP = p.css("p").extract()
                s = tempP[0].replace('<p class="">', "")
                s = s.replace("</p>", "")
                temp = temp + s

            for i in range(len(linksInArticle)):

                if linksInArticle[i] in temp:
                    temp = temp.replace(linksInArticle[i], linksTexts[i])

            replacedArticle = temp
        else:
            replacedArticle = response.css(".sz-article-body > p::text").extract()
            replacedArticle = replacedArticle[0]

        author = response.css(".sz-article-byline__author-link::text").get()
        published = response.css(".sz-article-header__time::text").get()

        items['title'] = title
        items['intro'] = intro
        items['article'] = replacedArticle
        items['author'] = author
        items["published"] = published
        items['summery'] = summery
        items['url'] = url
        items['department'] = dep

        yield items




    def scanDepartment(self, response, items, department):
        articls = response.css(".sz-teaser")
        links = articls.xpath("@href").extract()
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
        for i in range(len(links)):
            summery = articls[i].css(".sz-teaser__summary::text").get()
            yield scrapy.Request(links[i], callback=self.getArticle,
                                 cb_kwargs=dict(items=items, summery=summery, url=links[i], dep=department))

        offSet = 0
        more = "https://www.sueddeutsche.de/overviewpage/additionalDepartmentTeasers?departmentId={}&offset={}&size=50&isMobile=false".format(
            departmentIds[department], offSet)

        while offSet <= 1000:
            yield scrapy.Request(more, callback=self.scanDepartment, cb_kwargs=dict(items=items, department=department))
            offSet = offSet + 25
            more = "https://www.sueddeutsche.de/overviewpage/additionalDepartmentTeasers?departmentId={}&offset={}&size=50&isMobile=false".format(
                departmentIds[department], offSet)
