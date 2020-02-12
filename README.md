# <a name="english"></a>INews crawler
([German below](#german))

to crawl news websites, using [scrapy](https://scrapy.org/) framework .

The crawler is based on 'spiders' which crawl a specific news website and extract information.

every spider:
- crawls main page for category pages
- crawls all category pages for article links
- every crawled link is matched with database to avoid crawling duplicate articles 
- crawls article links for article and meta data (as defined in `items.py`)
- saves data in database in collection `scraped_articles` (via `pipelines.py`) 

using common methods in `utils.py`.

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

For execution you need to save the database authentification data in your `~/.profile`:

```
export MONGO_USER="s0..."
export MONGO_HOST="host:port
export MONGO_DATABASE="s0..."
export MONGO_PWD="password" 
``` 
 
 or save directly in `settings.py`.
 
 **Warning: If you save directly in `settings.py`, don't commit changes without removing your password!**

You also need access to the database (directly or via VPN)

More settings are available in `settings.py`, for example setting the mongoDB collection names.


### Test run

For a test run, you can limit each spider separately:

`testrun_cats = 3`    - limits the categories to crawl to this number. if zero, no limit.

`testrun_arts = 2`    - limits the article links to crawl to this number. if zero, no limit.

Execute in terminal (in folder crawler):

`scrapy crawl SPIDERNAME`  (sueddeutsche, taz, heise)

For example: `scrapy crawl taz`


### Deployment 

Don't forget to set the testrun variables to zero before pushing to git.

`git pull` the latest version into your server crawler directory.

If necessary, change in `settings.py` the database authentification data (as described in 'Setup') and mongoDB collection names.

Use `scrapyd-deploy` to deploy.

Read more:
- https://scrapyd.readthedocs.io/en/stable/
- https://github.com/scrapy/scrapyd-client#deploying-a-project

### Run spiders

The endpoint is set in `scrape.cfg`. 

To run a spider, you need to execute:
`curl http://localhost:6800/schedule.json -d project=inews_crawler -d spider=SPIDERNAME`

The script `scrape.sh` runs all three spiders.

For running the spiders regularily (like once a day) you can use a cron job. 


### Cron job

`crontab -l -u local` shows all cron jobs for user `local`

Editing is possible with `crontab -e`. 

`00 01 * * * /bin/sh /home/local/crawler/scrape.sh` will execute the spider script once a day at 1 a.m.


----------------------------------------------------------

### Spiders

#### 1) sueddeutsche

It is possible to crawl sueddeutsche articles way back in the past.

```limit_pages = 1```   sets the amount of additional category pages of 50 articles each, maximum of 400 pages.

For building the archive, you can use `400`, but for daily use `0` or `1` should be enough.
 
If you want to build the archive, please study the options in `settings.py` to slow down the spider.
Don't forget to set the testrun variables to zero.



#### 2) taz

There is no public archive accessible by pagination. Don't forget to set the testrun variables to zero.



#### 3) heise

It is possible to crawl heise articles way back in the past. 
```limit_pages = 1```   sets the amount of additional category pages of 15 articles each. 

For building the archive, you can use `0` to get the maximum amount of articles, but for daily use `3` or `4` should be enough.
 
If you want to build the archive, please study the options in `settings.py` to slow down the spider.
Don't forget to set the testrun variables to zero.


----------------------------------------------------------

### Logging

There are different levels of logging:
- DEBUG: scrapy events
- INFO: duplicate messages, database messages ("Post added to MongoDB", "already in db"), paywall message ("is paywalled")
- WARNING: property was not found ("Cannot parse title",...)
- ERROR: a function could not be executed
- CRITICAL: a serious error, indicating that the program itself may be unable to continue running

All logs will be saved here: `/logs/inews_crawler`

INFO and WARNING events will be also saved (via `utils.py`) as log items in the database in the collection 
`log_crawler`. 

    log_time            # datetime.now()
    url                 # String 'https://taz.de/!5642421/'
    news_site           # String: taz, sz, heise
    title               # String
    property            # String: text, title, keywords, ...
    level               # String: warning, info
    
This collection is connected to ElasticSearch and Kibana by executing `connector.py`. 
For running `connector.py`, it is necessary to have a file in the same directory containing 
the authentification data for mongoDB and ElasticSearch named `connector_secrets.py`:

    #!/usr/bin/env python3
    MONGO_USER = USER
    MONGO_HOST = HOSTNAME
    MONGO_DATABASE = DATABASE
    MONGO_PWD = PASSWORD
    MONGO_AUTH_MECHANISM = AUTH_MECHANISM
    
    MONGO_URI = 'mongodb://' + MONGO_USER + ':' + MONGO_PWD + '@' + MONGO_HOST \
                     + '/?authSource=' + MONGO_DATABASE + '&authMechanism=' + MONGO_AUTH_MECHANISM
    
    MONGO_COLLECTION = 'log_crawler'
    ELASTICSEARCH_HOST = 'localhost'
    ELASTICSEARCH_INDEX = 'mongo_log_crawler'

It makes sense to execute `connector.py` as cron job every time the spider cron job is finished. 
If the spiders are running at 1 a.m.,

`00 02 * * * /usr/bin/python3 /home/local/mongodb_connectors/scrape_log/connector.py` will execute the connector at 2 a.m.

### Kibana

Kibana is a tool which helps to visualize the logging data. 

There will be a certain amount of log entries with level  'warning', but if the warnings increase strongly 
the news site code might be changed and the spider code needs to be  adapted. 
If the amount of scraped articles is changing considerably, it might also be a pointing to altered code of the 
news site. In this case, check also the logs at `/logs/inews_crawler` for logs with level ERROR or CRITICAL. 

Log in via ssh and port forwarding:
`ssh -L 5601:localhost:5601 local@news.f4.htw-berlin.de`

If Kibana does not run, execute  
`systemctl start kibana`

Kibana will be accessible at http://localhost:5601

You can find the dashboard with 4 predefined visualizations 
[here](http://localhost:5601/goto/01b3034cb9c07768d317cbbbcf231ee4).

If you want to crawl more often than once a day, you can change each
[visualization](http://localhost:5601/app/kibana#/visualize) 
to other intervals by clicking `Buckets X-axis` and changing `Minimum interval` from daily to hourly and clicking `Save`.

----------------------------------------------------------

Happy crawling!

----------------------------------------------------------



# <a name="german"></a>INews Crawler
([English above](#english))

zum Crawlen von Newsseiten, nutzt das Framework [scrapy](https://scrapy.org/).

Der Crawler basiert auf 'Spider', die eine spezifische Newsseite crawlen und Informationen extrahieren.

Jeder Spider:
- crawlt die Hauptseite nach Kategorienseiten
- crawlt alle Kategorienseiten nach Links zu Artikeln
- jeder gefundene Link wird mit der Datenbank abgeglichen, um zu vermeiden, Artikel mehrfach zu crawlen. 
- crawlt die Artikellinks und extrahiert den Artikel und Metadaten (wie in `items.py` definiert)
- speichert die Daten in der Datenbank-Collection `scraped_articles` (via `pipelines.py`). 

und nutzt dabei jeweils gemeinsame Methoden in `utils.py`.


### Output in MongoDB

    crawl_time          # datetime.now()
    short_url           # String 'https://taz.de/!5642421/'
    long_url            # String 'https://taz.de/Machtkampf-in-Bolivien/!5642421/'

    news_site           # String: taz, sz, heise
    title               # String
    authors             # List(String)
    description         # String: Teaser für Artikel, manchmal derselbe Text wie Lead/Intro
    intro               # String: Lead/Intro, manchmal derselbe Text wie Description/Teaser
    text                # String

    keywords            # List(String) - sollte nicht die Newsseite selber beinhalten
    published_time      # datetime oder None
    image_links         # List(String)
    links               # List(String)

### Setup

Um den Crawler auszuführen, müssen die Datenbank-Authentifizierungsdaten in  `~/.profile` gespeichert werden:

```
export MONGO_USER="s0..."
export MONGO_HOST="host:port
export MONGO_DATABASE="s0..."
export MONGO_PWD="password" 
``` 
 
oder direkt in `settings.py` gespeichert werden.
 
 **Warnung: Wenn direkt in `settings.py` gespeichert wird, keine Commits machen ohne das Passwort zu entfernen!**

Es wird außerdem Zugang zur Datenbank benötigt (direkt oder via VPN)

Mehr Einstellungen sind möglich in `settings.py`, zum Beispiel die Namen der mongoDB-Collection.


### Testlauf

Für einen Testlauf kann jeder Spider einzeln begrenzt werden:

`testrun_cats = 3`    - begrenzt die Kategorien, die gecrawlt werden, auf diese Zahl. Bei 0 gibt es keine Begrenzung.

`testrun_arts = 2`    - begrenzt die Anzahl der Artikellinks, die gecrawlt werden, auf diese Zahl. Bei 0 gibt es keine Begrenzung.

Zum lokalen Ausführen kann im Terminal (im Order `crawler`) folgender Befehl benutzt werden:

`scrapy crawl SPIDERNAME`  (sueddeutsche, taz, heise)

Zum Beispiel: `scrapy crawl taz`


### Deployment 

Bitte nicht vergessen, die Testlauf-Variablen auf Null zu setzen, bevor in Git gepusht wird.

Mit `git pull` die letzte Version in das crawler-Verzeichnis auf dem Server laden.

Falls notwendig, können in `settings.py` die Datenbank-Authentifizierungs-Daten (wie bei 'Setup' beschrieben) und die 
Namen der mongoDB-Collection geändert werden. 

Mit `scrapyd-deploy` wird deployed.

Siehe auch:
- https://scrapyd.readthedocs.io/en/stable/
- https://github.com/scrapy/scrapyd-client#deploying-a-project


### Spider starten

Der Endpunkt ist in `scrape.cfg` konfiguriert. 

Zum Starten eines Spiders wird dieser Befehl ausgeführt:
`curl http://localhost:6800/schedule.json -d project=inews_crawler -d spider=SPIDERNAME`

Das Script `scrape.sh` führt alle drei Spider aus.

Um die Spider regelmäßig laufen zu lassen (z.B. einmal pro Tag), kann ein Cron-Job genutzt werden.


### Cron-Job

`crontab -l -u local` zeigt alle Cron-Jobs für User `local`

Die Cron-Jobs können mit `crontab -e` editiert werden. 

`00 01 * * * /bin/sh /home/local/crawler/scrape.sh` führt das Spider-Script einmal am Tag um 1 Uhr aus.


----------------------------------------------------------

### Spider

#### 1) sueddeutsche

Es ist möglich, Artikel aus der Süddeutschen Zeitung zu crawlen, die weit in der Vergangenheit publiziert wurden.

```limit_pages = 1```   bestimmt die Anzahl der zusätzlichen Kategorienseiten von jeweils 50 Artikeln, 
mit einem Maximum von 400 Seiten.

Um einen Grundstock an Artikeln zu bilden, kann mit `400` gecrawlt werden, im täglichen Gebrauch sollte `0` or `1` 
genug sein.

Wenn es um den Grundstock geht, können die Optionen in `settings.py` genutzt werden, um den Spider zu verlangsamen. 
Dabei nicht vergessen, die Testlauf-Variablen vorher auf Null zu setzen.



#### 2) taz

Bei der taz gibt es kein öffentliches Archiv. Die Testlauf-Variablen sollten im Normalbetrieb auch auf Null gesetzt sein.


#### 3) heise

Bei Heise ist es auch möglich, auf sehr alte Artikel zuzugreifen.
```limit_pages = 1```   bestimmt die Anzahl der zusätzlichen Kategorienseiten von jeweils 15 Artikeln. 

Um einen Grundstock an Artikeln zu bilden, kann mit `0` das Maximum an Artikeln gecrawlt werden. 
Im täglichen Gebrauch sollte `3` or `4` genug sein.

Wenn es um den Grundstock geht, können die Optionen in `settings.py` genutzt werden, um den Spider zu verlangsamen. 
Dabei nicht vergessen, die Testlauf-Variablen vorher auf Null zu setzen.


----------------------------------------------------------

### Logging

Es gibt verschiedene Level des Loggens:
- DEBUG: Scrapy-Events
- INFO: Nachrichten über Duplikate, die Datenbank betreffend ("Post added to MongoDB", "already in db"), 
die Paywall ("is paywalled")
- WARNING: Eine Property/ein Attribut wurde nicht gefunden ("Cannot parse title",...).
- ERROR: Eine Funktion konnte nicht ausgeführt werden.
- CRITICAL: Ein schwerer Fehler, eventuell kann das Programm nicht weiter ausgeführt werden.

Alle Logs werden auf dem Server hier gespeichert: `/logs/inews_crawler`

INFO- und WARNING-Events werden auch als Log-Items (via `utils.py`) in der Datenbank-Collection `log_crawler` 
gespeichert. 

    log_time            # datetime.now()
    url                 # String 'https://taz.de/!5642421/'
    news_site           # String: taz, sz, heise
    title               # String
    property            # String: text, title, keywords, ...
    level               # String: warning, info
    
Diese Collection ist mit ElasticSearch und Kibana durch das Ausführen von `connector.py` verbunden. 
Um `connector.py` ausführen zu können, ist es notwendig, dass im selben Verzeichnis eine Datei mit den 
Authentifizierungsdaten von mongoDB und ElasticSearch liegt, die `connector_secrets.py` benannt ist:

    #!/usr/bin/env python3
    MONGO_USER = USER
    MONGO_HOST = HOSTNAME
    MONGO_DATABASE = DATABASE
    MONGO_PWD = PASSWORD
    MONGO_AUTH_MECHANISM = AUTH_MECHANISM
    
    MONGO_URI = 'mongodb://' + MONGO_USER + ':' + MONGO_PWD + '@' + MONGO_HOST \
                     + '/?authSource=' + MONGO_DATABASE + '&authMechanism=' + MONGO_AUTH_MECHANISM
    
    MONGO_COLLECTION = 'log_crawler'
    ELASTICSEARCH_HOST = 'localhost'
    ELASTICSEARCH_INDEX = 'mongo_log_crawler'

Es macht Sinn, `connector.py` als Cron-Job jedes Mal auszuführen, wenn der Cron-Job der Spider beendet ist. 
Wenn die Spider um 1 Uhr laufen, führt

`00 02 * * * /usr/bin/python3 /home/local/mongodb_connectors/scrape_log/connector.py` den Connector um 2 Uhr aus.


### Kibana

Kibana ist ein Tool, das hier genutzt wird, um die Log-Daten zu visualisieren.

Es wird immer eine bestimmte Anzahl von Logeinträgen mit dem Level 'warning' geben, aber wenn die Anzahl von Warnungen 
stark anwächst, kann es sein, dass die Newsseite ihren HTML-Code geändert hat und der Code des Spiders ebenfalls 
angepasst werden muss. 
Wenn die Anzahl der gescrapten Artikel sich bedeutend ändert, deutet das auch auf eine Veränderung des Newsseiten-Codes
hin. In diesem Fall sollten auch die Logs unter `/logs/inews_crawler` nach Logeinträgen mit dem Level ERROR oder 
CRITICAL durchsucht werden. 

Login via SSH und Port Forwarding:

`ssh -L 5601:localhost:5601 local@news.f4.htw-berlin.de`

Wenn Kibana noch nicht läuft, startet es mit `systemctl start kibana`.

Kibana findet sich dann unter http://localhost:5601

Das Dashboard mit 4 vordefinierten Visualisierungen befindet sich 
[hier](http://localhost:5601/goto/01b3034cb9c07768d317cbbbcf231ee4).

Wenn mehr als einmal pro Tag gecrawlt werden soll, können die einzelnen 
[Visualisierungen](http://localhost:5601/app/kibana#/visualize) 
auf ein anderes Intervall geändert werden durch Anklicken von `Buckets X-axis` und verändern des `Minimum interval` von 
'daily' auf 'hourly', danach muss gespeichert werden.

----------------------------------------------------------

Happy crawling!
