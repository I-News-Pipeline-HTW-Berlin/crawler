# crawler
to crawl news websites


----------------------------------------------------------
## 1) sueddeutsche.de

coming soon



----------------------------------------------------------

## 2) taz.de

**a) taz_link_spider:**
- crawls all category pages for article links
- every crawled link is matched with database to avoid crawling duplicate articles 
(TODO via pipelines.py)

Execute in terminal (in folder crawler/lets):

`rm taz_links.json`

`scrapy crawl taz_links -o taz_links.json`


**b) taz_article_spider**
- removes duplicates in imported taz_links.json
- crawls article links for article and meta data (see items.py)
- saves data in database (TODO)

Execute in terminal (in folder crawler/lets):

`rm taz_articles.json`

`scrapy crawl taz_articles -o taz_articles.json`
