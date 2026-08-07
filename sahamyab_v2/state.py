from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


def _parse_last_run(info: dict[str, Any]) -> datetime:
    raw = info.get("last_run_at") or info.get("last_seen")
    if not raw:
        return datetime.min.replace(tzinfo=UTC)

    text = str(raw).strip()
    try:
        if len(text) == 8 and text.isdigit():
            return datetime.strptime(text, "%Y%m%d").replace(tzinfo=UTC)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def _tweet_count(info: dict[str, Any]) -> int:
    try:
        return max(0, int(info.get("last_run_tweet_count", 0)))
    except (TypeError, ValueError):
        return 0


class SymbolRegistry:
    """Preserves the complete hashtag registry and its crawl metadata."""

    def __init__(self, filename: str | Path) -> None:
        self.filename = Path(filename)
        if self.filename.exists():
            with self.filename.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        else:
            data = {}
        if not isinstance(data, dict):
            raise ValueError("symbols.json must contain a JSON object")
        self._symbols: dict[str, dict[str, Any]] = data

    def __len__(self) -> int:
        return len(self._symbols)

    def get(self, symbol: str) -> dict[str, Any]:
        return self._symbols.setdefault(symbol, {})

    def prioritized_symbols(self, limit: int | None = None) -> list[str]:
        """Oldest run first; higher previous new-tweet count breaks ties."""

        ordered = sorted(
            self._symbols,
            key=lambda symbol: (
                _parse_last_run(self._symbols[symbol]),
                -_tweet_count(self._symbols[symbol]),
                symbol,
            ),
        )
        if limit is None or limit <= 0:
            return ordered
        return ordered[:limit]

    def add_hashtags(self, hashtags: set[str], discovered_on: date) -> int:
        added = 0
        for hashtag in sorted(hashtags):
            if not hashtag or hashtag in self._symbols:
                continue
            self._symbols[hashtag] = {
                "first_seen": discovered_on.isoformat(),
                "last_run_tweet_count": 0,
            }
            added += 1
        return added

    def mark_success(
        self,
        symbol: str,
        *,
        run_at: datetime,
        new_tweet_count: int,
        newest_id: str | None,
    ) -> None:
        info = self.get(symbol)
        normalized = run_at.astimezone(UTC)
        info["last_seen"] = normalized.date().isoformat()
        info["last_run_at"] = normalized.isoformat().replace("+00:00", "Z")
        info["last_run_tweet_count"] = max(0, int(new_tweet_count))
        if newest_id is not None:
            info["last_id"] = str(newest_id)
        info.pop("last_run_error", None)
        info.pop("last_run_error_at", None)

    def mark_failure(self, symbol: str, *, run_at: datetime, error: str) -> None:
        info = self.get(symbol)
        normalized = run_at.astimezone(UTC)
        info["last_run_error_at"] = normalized.isoformat().replace("+00:00", "Z")
        info["last_run_error"] = error[:1000]

    def save(self) -> None:
        """Atomically replace symbols.json without dropping unknown fields."""

        self.filename.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.filename.parent,
                prefix=f".{self.filename.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_name = stream.name
                json.dump(
                    self._symbols,
                    stream,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, self.filename)
        except Exception:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise
