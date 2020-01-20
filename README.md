# INews crawler
to crawl news websites, using https://scrapy.org/

The crawler is based on 'spiders' which crawl a specific news website.

every spider:
- crawls all category pages for article links
- every crawled link is matched with database to avoid crawling duplicate articles 
- crawls article links for article and meta data (as defined in `items.py`)
- saves data in database in collection `scraped_articles` (via `pipelines.py`) 

### Output in MongoDB

    crawl_time          # datetime.now()
    short_url           # String 'https://taz.de/!5642421/'
    long_url            # String 'https://taz.de/Machtkampf-in-Bolivien/!5642421/'

    news_site           # String: taz, sz, heise
    title               # String
    authors             # List(String)
    description         # String: Teaser for article, sometimes same as lead/intro
    intro               # String: Lead/intro, sometimes same as description/teaser
    text                # String

    keywords            # List(String) - should not contain newssite
    published_time      # datetime or None
    image_links         # List(String)
    links               # List(String)

### Setup

For execution you need to save the database authentification data in your ~/.profile:

```
export MONGO_USER="s0..."
export MONGO_HOST="host:port
export MONGO_DATABASE="s0..."
export MONGO_PWD="password" 
``` 
 
 **Warning: If you save directly in `settings.py`, don't commit changes without removing your password!**

You also need access to the database (directly or via VPN)

More settings are available in `settings.py`, for example setting the collection.

### Test run

For a test run, you can limit each spider separately:

`testrun_cats = 3`    - limits the categories to crawl to this number. if zero, no limit.

`testrun_arts = 2`    - limits the article links to crawl to this number. if zero, no limit.

### Deployment 

don't forget to set the testrun variables to zero.

----------------------------------------------------------

### Spiders

#### 1) sueddeutsche.de

It is possible to crawl sueddeutsche articles way back in the past.

```limit_pages = 1```   sets the amount of additional category pages of 50 articles each, maximum of 400 pages.

For building the archive, you can use `400`, but for daily use `0` or `1` should be enough.
 
If you want to build the archive, please study the options in `settings.py` to slow down the spider.
Don't forget to set the testrun variables to zero.

execute in terminal (in folder crawler):

`scrapy crawl sueddeutsche`


#### 2) taz.de

execute in terminal (in folder crawler):

`scrapy crawl taz`


#### 3) heise.de

It is possible to crawl heise articles way back in the past. 
```limit_pages = 1```   sets the amount of additional category pages of 15 articles each. 

For building the archive, you can use `0` to get the maximum amount of articles, but for daily use `3` or `4` should be enough.
 
If you want to build the archive, please study the options in `settings.py` to slow down the spider.
Don't forget to set the testrun variables to zero.



execute in terminal (in folder crawler):

`scrapy crawl heise`

----------------------------------------------------------

### Logging

- DEBUG: scrapy events
- INFO: duplicate messages, database messages ("Post added to MongoDB", "already in db"), paywall message ("is paywalled")
- WARNING: property was not found ("Cannot parse title",...)

INFO and WARNING events will be saved as log items in the database in the collection `log_crawler`, which is connected to ElasticSearch and Kibana by executing `connector.py`.

    log_time            # datetime.now()
    url                 # String 'https://taz.de/!5642421/'
    news_site           # String: taz, sz, heise
    title               # String
    property            # String: text, title, keywords, ...
    level               # String: warning, info

----------------------------------------------------------

Happy crawling!