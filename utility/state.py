from __future__ import annotations

import json
from pathlib import Path


class SymbolState:

    def __init__(self, filename: str | Path = "symbols.json"):

        self.filename = Path(filename)

        with open(self.filename, "r", encoding="utf-8") as f:
            self._symbols = json.load(f)

    def symbols(self):

        return self._symbols.items()

    def exists(self, symbol: str) -> bool:

        return symbol in self._symbols

    def get(self, symbol: str) -> dict:

        return self._symbols.setdefault(symbol, {})

    def first_seen(self, symbol: str) -> str:

        return self.get(symbol).get("first_seen", "")

    def last_seen(self, symbol: str) -> str:

        return self.get(symbol).get("last_seen", "19000101")

    def last_id(self, symbol: str) -> int | None:

        return self.get(symbol).get("last_id")

    def update(
        self,
        symbol: str,
        *,
        last_seen: str | None = None,
        last_id: int | None = None,
    ):

        info = self.get(symbol)

        if last_seen is not None:
            info["last_seen"] = last_seen

        if last_id is not None:
            info["last_id"] = last_id

    def save(self):

        with open(self.filename, "w", encoding="utf-8") as f:

            json.dump(
                self._symbols,
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
