# crawler
to crawl news websites


**Warning: Don't commit changes in settings.py without removing your password!**

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
- saves data in database in collection 'scraped_articles'

For execution you need to fill in the database authentification data in settings.py. 
Warning: Don't commit changes in settings.py without removing your password!
 
If you have access to the database (directly or via VPN), 
execute in terminal (in folder crawler/lets):

`scrapy crawl taz_articles`