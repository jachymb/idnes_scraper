from datetime import datetime
from pony.orm import *


db = Database()


class Article(db.Entity):
    id = PrimaryKey(int, auto=True)
    url = Required(str, unique=True)
    headline = Required(str)
    opener = Optional(str)
    body = Required(str)
    published = Required(datetime)
    modified = Optional(datetime)
    tags = Set('Tag')
    comments = Set('Comment')
    #download_latency = Required(float)
    #download_timeout = Required(float)


class Tag(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=True)
    articles = Set(Article)


class Comment(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required('User')
    article = Required(Article)
    text = Required(str)
    timestamp = Required(datetime)
    upvotes = Required(int)
    downvotest = Required(int)


class User(db.Entity):
    id = PrimaryKey(int)
    name = Optional(str)
    comments = Set(Comment)


db.bind("sqlite", "database.sqlite", create_db=True)
db.generate_mapping(create_tables=True)
