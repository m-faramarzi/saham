import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime
from extract_news_text import parse_boursenews_text

BASE_URL = "https://www.boursenews.ir"

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_news_links(html):

    soup = BeautifulSoup(html, "html.parser")

    links = []

    for item in soup.select("div.linearNewsItem"):

        a = item.select_one("a.linNewsLink")

        if a is None:
            continue

        href = a.get("href")

        if not href:
            continue

        title = a.select_one("h4.linearNewsTxt")

        links.append(
            {
                "id": href.split("/")[3],
                "title": title.get_text(strip=True) if title else "",
                "url": urljoin(BASE_URL, href),
            }
        )

    return links


# -----------------------------
# append jsonl
# -----------------------------
def append_json(item):
    filename = f"news/{datetime.now():%Y%m%d}_{item["category"]}.json"

    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    with open(filename, "a", encoding="utf-8") as f:

        json.dump(item, f, ensure_ascii=False)

        f.write("\n")


# -----------------------------
# main
# -----------------------------
def crawl_archive(archive_url):

    r = requests.get(archive_url, headers=HEADERS)

    links = get_news_links(r.text)

    for link in links:

        try:

            print(link)

            news = parse_boursenews_text(link["url"])

            append_json(news)

        except Exception as e:

            print(e)


if __name__ == "__main__":

    archives = [
        "https://www.boursenews.ir/fa/archive?service_id=1&sec_id=-1&cat_id=-1&rpp=100",
        "https://www.boursenews.ir/fa/archive?service_id=14&sec_id=-1&cat_id=-1&rpp=100",
        "https://www.boursenews.ir/fa/archive?service_id=3&sec_id=-1&cat_id=-1&rpp=100",
        "https://www.boursenews.ir/fa/archive?service_id=4&sec_id=-1&cat_id=-1&rpp=100",
    ]

    for arch in archives:
        for page in range(100):
            url = f"{arch}" + f"&p={page+1}"
            crawl_archive(url)
