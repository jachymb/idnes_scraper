# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from itertools import count
from idnes.dbmodel import *
from datetime import datetime
from functools import partial
import logging

@db_session
def create_comment(comment_item, article):
    try:
        user = User[comment_item["user_id"]]
    except ObjectNotFound:
        user = User(id=comment_item["user_id"], name=comment_item["user_name"])

    timestamp = datetime.strptime(comment_item["timestamp"] ,"%d.%m.%Y %H:%M")
    
    return Comment(
        user = user,
        text = comment_item["text"],
        upvotes = comment_item["upvotes"],
        downvotest = comment_item["downvotes"],
        timestamp = timestamp,
        article = article)

@db_session
def get_tag(name):
    return Tag.get(name=name) or Tag(name=name)

class IdnesPipeline:
    counter = count(1)

    @db_session
    def process_item(self, item, spider):
        time_format = "%Y-%m-%dT%H:%M:%S"

        for key in ("body","headline"):
            if not item[key]:
                logging.warning("Article without %s at: %s!" % (key, item["url"]))
                return item 

        article = Article(
            url=item["url"],
            headline=item["headline"],
            opener=item["opener"],
            body=item["body"],
            published=datetime.strptime(item["published"], time_format),
            modified=datetime.strptime(item["modified"], time_format))

        for tag_name in item["tags"]:
            get_tag(tag_name).articles.add(article)
        
        for comment in item["comments"]:
            if comment["text"]:
                create_comment(comment, article)

        return item

