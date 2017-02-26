import scrapy
import logging
from urllib.parse import parse_qs, urlparse

def s_extract(node, xpath):
    s, = node.xpath(xpath).extract()
    return " ".join(s.split())

def p_extract(node, xpath):
    return "\n".join(
        s_extract(paragraph, "string(.)")
        for paragraph in node.xpath(xpath))

BASE_URL = "http://zpravy.idnes.cz"

class IDnesSpider(scrapy.Spider):
    name = 'idnes'
    start_urls = [BASE_URL]

    def parse(self, response):
        # Extract links to other articles
        for article_link in response.css(".art"):
            for href in article_link.xpath(".//a/@href").extract():
                if href.startswith(BASE_URL):
                    yield scrapy.Request(href, callback=self.parse)

        if response.url == BASE_URL: return

        # Extract article content
        # could also use <meta property="og: ... for headline, tags, opener
        try:
            content, = response.css("#content")
            headline = s_extract(content, "string(./div[@class='space-a']//h1)")
            opener = s_extract(content, "string(./div[@class='space-a']//div[@class='opener'])")
            body = p_extract(content, "./div[@class='space-b']//div[@id='art-text']//p")
            published = s_extract(response, "string(//meta[@property='article:published_time']/@content)")
            modified = s_extract(response, "string(//meta[@property='article:modified_time']/@content)")
            tags = [s_extract(node, "string(.)")
                    for node
                    in content.xpath("./div[@class='space-b']//div[@id='art-tags']/a")]

        except ValueError as ex:
            logging.exception("ValueError in article parsing at: " + response.url)

        else:
            article_data = {
                    "url": response.url,
                    "headline": headline,
                    "opener": opener,
                    "body": body,
                    "published": published,
                    "modified": modified,
                    "tags": tags,
                    "comments": []}
            
            comments_href = s_extract(content, "string(.//a[@id='moot-linkin']/@href)")
            yield scrapy.Request(BASE_URL + comments_href, callback=self.parse_comments, meta=article_data)

    def parse_comments(self, response):
        article_data = response.meta
        for comment in response.css(".contribution"):
            name = "".join(comment.xpath(".//h4[@class='name']/a/text()").extract())
            try:
                user_id = int("".join(comment.xpath(".//h4[@class='name']/sup/text()").extract()))
                text = p_extract(comment, ".//div[@class='user-text']")
                upvotes, downvotes = (int(x.strip().replace("\u2212","-"))
                    for x in comment.xpath(".//div[@class='score']//span/text()").extract())
                timestamp = s_extract(comment, ".//div[@class='date hover']/text()")
            except ValueError as ex:
                logging.debug("ValueError in comment parsing at: " + response.url)
                break # Probably old format

            article_data["comments"].append({
                    "user_name": name,
                    "user_id": user_id,
                    "text": text,
                    "timestamp": timestamp,
                    "upvotes": upvotes,
                    "downvotes": downvotes})
        else:
            next_page = response.xpath(".//a[@title='další']/@href").extract()
            if next_page:
                yield scrapy.Request(next_page[0], callback=self.parse_comments, meta=article_data)
            else:
                yield article_data
