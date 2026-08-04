from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class TweetWriter:

    def __init__(
        self,
        symbol: str,
        snapshot_root: str | Path = "snapshots",
        snapshot_date: date | None = None,
    ):

        self.symbol = symbol

        self.snapshot_date = snapshot_date or date.today()

        folder = (
            Path(snapshot_root)
            / self.snapshot_date.strftime("%Y")
            / self.snapshot_date.strftime("%m")
            / self.snapshot_date.strftime("%d")
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = folder / f"{self.snapshot_date.strftime('%Y%m%d')}_{symbol}.json"

        self.file = open(
            filename,
            "a",
            encoding="utf-8",
        )

        self.count = 0

    def append(self, tweet: dict):

        json.dump(
            tweet,
            self.file,
            ensure_ascii=False,
        )

        self.file.write("\n")

        self.count += 1

    def append_many(self, tweets: list[dict]):

        for tweet in tweets:
            self.append(tweet)

    def flush(self):

        self.file.flush()

    def close(self):

        self.file.close()

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.close()
