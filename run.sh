#!/bin/sh
OUTFILE=idnes.json
[ -f $OUTFILE ] && rm $OUTFILE
scrapy crawl idnes -o $OUTFILE -L WARNING
