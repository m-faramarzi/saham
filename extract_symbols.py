import json
import re
from pathlib import Path
from datetime import datetime,date

SNAPSHOT_DIR = Path("snapshots")
SYMBOL_FILE = Path("symbols.json")


HASHTAG_PATTERN = re.compile(r"#([\u0600-\u06FFa-zA-Z0-9_]+)")


def load_symbols():

    if SYMBOL_FILE.exists():
        with open(SYMBOL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def save_symbols(db):

    with open(SYMBOL_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2, sort_keys=True)


def process_file(path, db):

    print(f"Reading {path}")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()

            if not line:
                continue

            tweet = json.loads(line)

            text = tweet.get("content", "")
            ##send_time = tweet["sendTime"][:10]
            send_time = date.today().isoformat()

            hashtags = HASHTAG_PATTERN.findall(text)

            for symbol in hashtags:

                symbol = symbol.strip()

                if not symbol:
                    continue

                if symbol not in db:

                    db[symbol] = {"first_seen": send_time, "last_seen": send_time}


def main():

    db = load_symbols()

    files = sorted(SNAPSHOT_DIR.rglob("*.json"))

    print(f"{len(files)} snapshot files found")

    for file in files:
        process_file(file, db)

    save_symbols(db)

    print(f"{len(db)} unique symbols saved.")


if __name__ == "__main__":
    main()
