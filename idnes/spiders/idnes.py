import scrapy
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
        content, = response.css("#content")
        # could also use <meta property="og: ... for headline, tags, opener
        headline = s_extract(content, "string(./div[@class='space-a']//h1)")
        opener = s_extract(content, "string(./div[@class='space-a']//div[@class='opener'])")
        body = p_extract(content, "./div[@class='space-b']//div[@id='art-text']//p")
        published = s_extract(response, "string(//meta[@property='article:published_time']/@content)")
        modified = s_extract(response, "string(//meta[@property='article:modified_time']/@content)")
        tags = [s_extract(node, "string(.)")
                for node
                in content.xpath("./div[@class='space-b']//div[@id='art-tags']/a")]

        article_data = {
                "url": response.url,
                "headline": headline,
                "opener": opener,
                "body": body,
                "published": published,
                "modified": modified,
                "tags": tags}
        
        comments_href = s_extract(content, "string(.//a[@id='moot-linkin']/@href)")
        yield scrapy.Request(BASE_URL + comments_href, callback=self.parse_comments, meta=article_data)
        # Extract comment section

    def parse_comments(self, response):
        comments_data = []

        for comment in response.css(".contribution"):
            name = "".join(comment.xpath(".//h4[@class='name']/a/text()").extract())
            try:
                user_id = int("".join(comment.xpath(".//h4[@class='name']/sup/text()").extract()))
            except ValueError:
                break # No user id = article too old

            text = p_extract(comment, ".//div[@class='user-text']")
            upvotes, downvotes = (int(x.strip().replace("\u2212","-"))
                for x in comment.xpath(".//div[@class='score']//span/text()").extract())
            timestamp = s_extract(comment, ".//div[@class='date hover']/text()")

            comments_data.append({
                    "user_name": name,
                    "user_id": user_id,
                    "text": text,
                    "timestamp": timestamp,
                    "upvotes": upvotes,
                    "downvotes": downvotes})

        article_data = response.meta
        article_data["comments"] = comments_data
        yield article_data
