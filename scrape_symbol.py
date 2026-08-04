import json
from datetime import datetime, date, timedelta
import time
from pathlib import Path
import requests
import random
import traceback


class SahamyabCrawler:
    URL = "https://www.sahamyab.com/guest/twiter/list?v=0.1"

    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json",
    }

    def build_file(self, symbol: str) -> str:
        now = date.today()
        self.folder = (
            Path("snapshots")
            / now.strftime("%Y")
            / now.strftime("%m")
            / now.strftime("%d")
        )
        self.folder.mkdir(parents=True, exist_ok=True)
        file_name = self.folder / f"{now.strftime('%Y%m%d')}_{symbol}.json"
        return file_name

    def post_request(self, payload: dict[str:str]):
        attempt = 0
        success_post = False
        while attempt < 5 and not success_post:
            r = requests.post(self.URL, headers=self.HEADERS, json=payload, timeout=30)
            if r.status_code == 200:
                success_post = True
            else:
                attempt += 1
                print(f"attempt {attempt} -> {r.status_code}")
                time.sleep(random.randint(10, 30))

        if attempt == 5:
            return None

        r.raise_for_status()
        return r
    def remove_deuplicate(self,items,previous_last_id):        

        for i, item in enumerate(items):
            if item["id"] == previous_last_id:
                del items[i:]
                return True
        return False
    
    def fetch_symbol(self, symbol: str, file_name: str, previous_last_id: str) :
        page = 0
        tweets = []
        curent_last_id =None
        last_id = None
        while page < 11:
            if page == 0:
                payload = {"page": page, "tag": symbol}
            else:
                payload = {"page": page, "tag": symbol, "id": last_id}
            r = self.post_request(payload)
            if not r:
                break
            data = r.json()
            items = data["items"]

            if not data.get("hasMore", False):
                break
            if not items:
                break
            
            has_duplicate = self.remove_deuplicate(items,previous_last_id)
            tweets.extend(items)
            if has_duplicate:
                break

            print(f"page={page}  symbol={symbol}  tweets={len(items)}")
            last_id = items[-1]["id"]
            page += 1
            time.sleep(random.randint(1, 3))
        if len(tweets)>0:
            curent_last_id = tweets[0]["id"]
            self.append_items(file_name, tweets)
            return curent_last_id
        else:
            return previous_last_id

        

    def append_items(self,file_name: str, items: list):
        with open(file_name, "a", encoding="utf-8") as f:
            for item in items:
                json.dump(item, f, ensure_ascii=False)
                f.write("\n")

    def process_symbols(self):
        SYMBOL_FILE = Path("symbols.json")
        with open(SYMBOL_FILE, "r", encoding="utf-8") as f:
            symbols = json.load(f)

        today = date.today()
        tomorrow = today + timedelta(days=1)

        today_str = today.isoformat()
        tomorrow_str = tomorrow.isoformat()
        processed_symbols = 1
        for symbol, info in symbols.items():
            if processed_symbols > 150:
                return
            last_seen = info.get("last_seen", "20260701")
            last_id = info.get("last_id", "1")
            if last_seen <= today_str:
                processed_symbols = processed_symbols + 1
                file_name = self.build_file(symbol)
                last_id = self.fetch_symbol(symbol, file_name, last_id)

                info["last_seen"] = tomorrow_str
                info["last_id"] = last_id
                with open(SYMBOL_FILE, "w", encoding="utf-8") as f:
                    json.dump(symbols, f, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    try:
        crawler = SahamyabCrawler()
        crawler.process_symbols()
    except Exception:
        traceback.print_exc()
        raise
