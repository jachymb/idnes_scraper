#!/bin/sh
OUTFILE=idnes.json
[ -f $OUTFILE ] && rm $OUTFILE
rm idnes/database.sqlite
scrapy crawl idnes -o $OUTFILE -L INFO
