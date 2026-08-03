import re
from model.news_item import NewsItem
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utility.base_crawler import BaseCrawler
from utility.jalali_date_parser import JalaliDateParser


class SenaCrawler(BaseCrawler):
    BASE_URL = "https://www.sena.ir"
    SOURCE :str = 'sena'
   
    
    def extract_links(self, url: str) -> list[NewsItem]:
        req = requests.get(url, headers=self.HEADERS)
        
        soup = BeautifulSoup(req.text, "html.parser")
        
        newslinks = []
        items = soup.select_one("div.archive_content")
            
        if items is None:
            raise Exception("No archive") 
            
        for item in items.select("div.linearNewsItem"):
        
            a = item.select_one("a.linNewsLink")
        
            if a is None:
                continue
        
            href = a.get("href")
        
            if not href:
                continue
        
            title = a.select_one("h4.linearNewsTxt")
            news = NewsItem(
                source=self.SOURCE,
                id=href.split("/")[3],
                title=title.get_text(strip=True) if title else "",
                news_url=urljoin(self.BASE_URL, href)
            )
            newslinks.append(news)
        
        return newslinks
            
    def scrape_page(self, news_item:NewsItem) -> NewsItem:                

        req = requests.get(news_item.news_url, headers=self.HEADERS, timeout=30)
        req.raise_for_status()
        
        soup = BeautifulSoup(req.text, "html.parser")

        
        article = soup.select_one("article#item")

        # ------------------------
        # news id
        # ------------------------

        m = re.search(r"/news/(\d+)/", news_item.news_url)
        news_item.id = m.group(1)

        # ------------------------
        # title
        # ------------------------

        subtitle = article.select_one("h4.subtitle")
        title = article.select_one("h1.title")

        title_text = ""

        if subtitle:
            title_text = subtitle.get_text(" ", strip=True) + ' _ ' 
        title_text += title.get_text(" ", strip=True)
        news_item.title = title_text

        # ------------------------
        # category
        # ------------------------

        breadcrumbs = article.select(".breadcrumb li a")

        category = ""

        if len(breadcrumbs) >= 2:
            category = breadcrumbs[1].get_text(strip=True)
        elif breadcrumbs:
            category = breadcrumbs[0].get_text(strip=True)

        # ------------------------
        # type
        # ------------------------

        type_node = article.select_one(".breadcrumb li:first-child a")

        news_type = (
            type_node.get_text(strip=True)
            if type_node
            else ""
        )

        # ------------------------
        # publish datetime
        # ------------------------

        date_node = article.select_one(".item-date span")

        jalali_datetime = ""

        if date_node:
            text = date_node.get_text(" ", strip=True)
            text = re.sub(r"^\s*", "", text)
            text = text.replace(" - ", " ")
            jalali_datetime = text.replace("۱۱ مرداد ۱۴۰۵ ۱۰:۴۳",
                                           text)

        parsed = JalaliDateParser.parse(jalali_datetime)

        # ------------------------
        # body
        # ------------------------

        body_div = article.select_one(".item-text")

        paragraphs = []

        if body_div:

            for p in body_div.find_all("p", recursive=False):

                txt = p.get_text(" ", strip=True)

                if txt:
                    paragraphs.append(txt)

        body = "\n\n".join(paragraphs)

        # ------------------------
        # author
        # ------------------------

        author_node = article.select_one(".item-author .name")

        author = None

        if author_node:
            author = author_node.get_text(strip=True)

        # ------------------------
        # tags
        # ------------------------

        tags = [
            x.get_text(strip=True)
            for x in article.select(".tags li a")
        ]

        # ------------------------
        # short url
        # ------------------------

        short_url = ""

        short_node = article.select_one("#short-url")

        if short_node:
            short_url = short_node.get("value", "")

        # ------------------------

        return NewsItem(

            source=self.SOURCE,

            news_id=news_id,

            title=title_text,

            category=category,

            type=news_type,

            publish_date_jalali=parsed.date_jalali,

            publish_datetime_jalali=parsed.datetime_jalali,

            publish_date_gregorian=parsed.date_gregorian,

            publish_datetime_gregorian=parsed.datetime_gregorian,

            author=author,

            tags=tags,

            short_url=short_url,

            news_url=url,

            body=body,

            crawl_time=datetime.utcnow(),
        )