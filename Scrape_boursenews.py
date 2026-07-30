import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://www.boursenews.ir"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_news_links(archive_url):

    r = requests.get(archive_url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    seen = set()

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if not href.startswith("/fa/news/"):
            continue

        url = urljoin(BASE_URL, href)

        if url in seen:
            continue

        seen.add(url)
        links.append(url)

    return links


# -----------------------------
# استخراج اطلاعات یک خبر
# -----------------------------
def parse_news(url):

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # ---------- id ----------
    m = re.search(r"/news/(\d+)/", url)
    news_id = m.group(1) if m else ""

    # ---------- title ----------
    title = ""

    if soup.find("h1"):
        title = soup.find("h1").get_text(" ", strip=True)

    # ---------- متن خبر ----------
    content = ""

    article = (
        soup.find("div", class_=re.compile("news|content|body", re.I))
        or soup.find("article")
    )

    if article:
        content = article.get_text("\n", strip=True)

    # ---------- تاریخ ----------
    publish_date = ""

    txt = soup.get_text(" ", strip=True)

    m = re.search(r"\d{4}/\d{2}/\d{2}", txt)

    if m:
        publish_date = m.group()

    # ---------- category ----------
    category = ""

    for a in soup.find_all("a", href=True):

        if "/archive?" in a["href"]:

            t = a.get_text(strip=True)

            if len(t) < 40:
                category = t
                break

    item = {
        "id": news_id,
        "title": title,
        "publish_date": publish_date,
        "category": category,
        "type": "news",
        "url": url,
        "content": content
    }

    return item


# -----------------------------
# append jsonl
# -----------------------------
def append_jsonl(filename, item):

    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    with open(filename, "a", encoding="utf-8") as f:

        json.dump(item, f, ensure_ascii=False)

        f.write("\n")


# -----------------------------
# main
# -----------------------------
def crawl_archive(archive_url):

    outfile = f"news/{datetime.now():%Y%m%d}.jsonl"

    links = get_news_links(archive_url)

    print(f"{len(links)} links found")

    for i, link in enumerate(links, 1):

        try:

            print(i, link)

            news = parse_news(link)

            append_jsonl(outfile, news)

        except Exception as e:

            print(e)


if __name__ == "__main__":

    archive = "https://www.boursenews.ir/fa/archive?service_id=1&sec_id=279&cat_id=-1&rpp=100&p=1"

    crawl_archive(archive)
    