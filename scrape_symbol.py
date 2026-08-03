import gzip
import json
from datetime import datetime, date, timedelta

import time
from pathlib import Path
import requests
import random
import traceback

URL = "https://www.sahamyab.com/guest/twiter/list?v=0.1"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json",
}


def fetch_symbol(symbol):
    page = 0
    tweets = []
    now = date.today()
    folder = (
        Path("snapshots") / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    )
    folder.mkdir(parents=True, exist_ok=True)

    filename = folder / f"{now.strftime('%Y%m%d')}_{symbol}.json"
    last_id = None
    while page < 11:
        if page == 0:
            payload = {"page": page, "tag": symbol}
        else:
            payload = {"page": page, "tag": symbol, "id": last_id}

        r = requests.post(URL, headers=HEADERS, json=payload, timeout=30)

        r.raise_for_status()

        data = r.json()
        items = data["items"]

        if not data.get("hasMore", False):
            return

        tweets.extend(items)

        print(f"page={page}  symbol={symbol}  tweets={len(items)}")
        append_items(filename, items)

        if not items:
            return
        
        last_id = items[-1]["id"]
        page += 1
        time.sleep(random.randint(1, 3))

    return 0


def append_items(filename, items):
    with open(filename, "a", encoding="utf-8") as f:
        for item in items:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")


def process_symbols():
    SYMBOL_FILE = Path("symbols.json")
    with open(SYMBOL_FILE, "r", encoding="utf-8") as f:
        symbols = json.load(f)

    today = date.today()
    tomorrow = today + timedelta(days=1)

    today_str = today.isoformat()
    tomorrow_str = tomorrow.isoformat()
    CC = 1
    for symbol, info in symbols.items():
        if CC > 150:
            return
        last_seen = info.get("last_seen", "1900-01-01")
        
        if last_seen <= today_str:
            CC = CC + 1
            fetch_symbol(symbol)

            info["last_seen"] = tomorrow_str
            with open(SYMBOL_FILE, "w", encoding="utf-8") as f:
                json.dump(symbols, f, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    try:
        process_symbols()
    except Exception:
        traceback.print_exc()
        raise   
