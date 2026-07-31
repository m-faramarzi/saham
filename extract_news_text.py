import re
import requests
import jdatetime
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

MONTHS = {
    "فروردین": 1,
    "اردیبهشت": 2,
    "خرداد": 3,
    "تیر": 4,
    "مرداد": 5,
    "شهریور": 6,
    "مهر": 7,
    "آبان": 8,
    "آذر": 9,
    "دی": 10,
    "بهمن": 11,
    "اسفند": 12,
}


def fa_to_en(text):
    return text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))


def extract_dates(soup):

    tag = soup.select_one("div.newsDate")

    if tag is None:
        return "", ""

    txt = fa_to_en(tag.get_text(" ", strip=True))

    m = re.search(r"(\d{2})\s+(\S+)\s+(\d{4})\s*-\s*(\d{2}:\d{2})", txt)

    if m is None:
        return "", ""

    day = int(m.group(1))
    month = MONTHS[m.group(2)]
    year = int(m.group(3))
    time = m.group(4)

    jalali = f"{year:04d}-{month:02d}-{day:02d} {time}"

    g = jdatetime.datetime(year, month, day, int(time[:2]), int(time[3:])).togregorian()

    gregorian = g.strftime("%Y-%m-%d %H:%M:%S")

    return jalali, gregorian


def parse_boursenews_text(url):

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # ---------------- id ----------------

    m = re.search(r"/news/(\d+)/", url)
    news_id = m.group(1) if m else ""

    # ---------------- title ----------------

    title = ""

    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)

    # ---------------- category ----------------

    category = ""

    tag = soup.select_one("a.newsServiceName")

    if tag:
        category = tag.get_text(strip=True)

    # ---------------- type ----------------

    news_type = ""

    tag = soup.select_one("a.newsSubjectName")

    if tag:
        news_type = tag.get_text(strip=True)

    # ---------------- short url ----------------

    short_url = url

    tag = soup.select_one("div.link_shortlink input")

    if tag:
        short_url = tag.get("value", "").strip()

    # ---------------- dates ----------------

    jalali_date, gregorian_date = extract_dates(soup)

    # ---------------- remove unwanted ----------------

    for t in soup(["script", "style", "nav", "footer", "header", "aside"]):
        t.decompose()

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
        for t in soup.select(css):
            t.decompose()

    # ---------------- text ----------------

    paragraphs = []

    for p in soup.find_all("p"):

        txt = p.get_text(" ", strip=True)

        if len(txt) < 3:
            continue

        paragraphs.append(txt)

    text = "\n\n".join(paragraphs)

    return {
        "id": news_id,
        "title": title,
        "category": category,
        "type": news_type,
        "publish_date_jalali": jalali_date,
        "publish_date": gregorian_date,
        "url": short_url,
        "text": text,
    }
