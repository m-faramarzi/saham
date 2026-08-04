import re
from model.news_item import NewsItem
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utility.base_crawler import BaseCrawler
from utility.jalali_date_parser import JalaliDateParser


class BourseNewsCrawler(BaseCrawler):
    BASE_URL = "https://www.boursenews.ir"
    SOURCE: str = "boursenews"

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
                news_url=urljoin(self.BASE_URL, href),
            )
            newslinks.append(news)

        return newslinks

    def scrape_page(self, news_item: NewsItem) -> NewsItem:

        req = requests.get(news_item.news_url, headers=self.HEADERS, timeout=30)
        req.raise_for_status()

        soup = BeautifulSoup(req.text, "html.parser")

        # ---------------- id ----------------

        news_id = re.search(r"/news/(\d+)/", news_item.news_url)
        news_item.id = news_id.group(1) if news_id else ""

        # ---------------- title ----------------

        h1 = soup.find("h1")

        if h1:
            news_item.title = h1.get_text(" ", strip=True)

        # ---------------- category ----------------

        tag = soup.select_one("a.newsServiceName")

        if tag:
            category = tag.get_text(strip=True)
            category = re.sub(r'[\\/:*?"<>|]', "_", category)
            news_item.category = (
                category.replace("\u200c", "").replace("\u200f", "").strip()
            )

        # ---------------- type ----------------

        tag = soup.select_one("a.newsSubjectName")

        if tag:
            news_item.type = tag.get_text(strip=True)

        # ---------------- short url ----------------

        tag = soup.select_one("div.link_shortlink input")

        if tag:
            news_item.short_url = tag.get("value", "").strip()

        # ---------------- dates ----------------
        tag = soup.select_one("div.newsDate")
        date_text = tag.get_text(" ", strip=True)
        news_item.publish_date_j, news_item.publish_date_g = JalaliDateParser.parse(
            date_text, "WEEKDAY DD MONTH YYYY - HH24:MI"
        )
        # ------------------tags ---------------------------
        tags = [a.get_text(strip=True) for a in soup.select("div.newsTags a.tags_item")]
        news_item.tags = tags

        # ---------------- remove unwanted ----------------

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # حذف divهای اضافی
        for css in [
            ".link_shortlink",
            ".newsTagsItems",
            ".shareBox",
            ".relatedNews",
            ".commentBox",
            ".advertise",
            ".banner",
            ".ads",
        ]:
            for tag in soup.select(css):
                tag.decompose()

        # ---------------- text ----------------

        paragraphs = []

        for paragraph in soup.find_all("p"):

            text = paragraph.get_text(" ", strip=True)

            if len(text) < 3:
                continue

            paragraphs.append(text)

        text = "\n\n".join(paragraphs)
        if text.startswith("بورس نیوز:"):
            text = text[len("بورس نیوز:") :].strip()
        news_item.body = text

        return news_item
