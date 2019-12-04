#!/bin/bash

curl http://localhost:6800/schedule.json -d project=inews_crawler -d spider=sueddeutsche
curl http://localhost:6800/schedule.json -d project=inews_crawler -d spider=taz