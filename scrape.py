import gzip
import json
from datetime import datetime
import time
from pathlib import Path
import requests
import random

URL = "https://www.sahamyab.com/guest/twiter/list?v=0.1"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json",
}


def fetch_all():
    page = 0
    tweets = []
    now = datetime.utcnow()
    folder = Path("snapshots") / now.strftime("%Y") / now.strftime("%m")
    folder.mkdir(parents=True, exist_ok=True)
    filename = folder / now.strftime("%Y-%m-%d_%H-%M-%S.json")    
    while page < 11:
        if page == 0:
            payload = {"page": page}
        else:
            payload = {"page": page, "id": id}

        r = requests.post(URL, headers=HEADERS, json=payload, timeout=30)

        r.raise_for_status()

        data = r.json()
        items = data["items"]

        tweets.extend(items)

        print(f"page={page}  tweets={len(items)}")
        append_items(filename, items)

        id = items[9]["id"]
        page += 1
        time.sleep(random.randint(5, 30))

    return tweets


def append_items(filename, items):
    with open(filename, "a", encoding="utf-8") as f:
        for item in items:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")


if __name__ == "__main__":

    tweets = fetch_all()
