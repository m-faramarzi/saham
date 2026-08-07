from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .models import TweetItem


@dataclass(frozen=True, slots=True)
class StoreResult:
    fetched_count: int
    new_for_symbol_count: int
    globally_new_count: int
    updated_count: int
    unchanged_count: int


class SqliteTweetStore:
    """Canonical, transactional and idempotent Sahamyab tweet store."""

    def __init__(self, filename: str | Path) -> None:
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.filename)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                send_time TEXT NOT NULL,
                payload TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS symbol_tweets (
                symbol TEXT NOT NULL,
                tweet_id TEXT NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (symbol, tweet_id)
            );

            CREATE INDEX IF NOT EXISTS ix_symbol_tweets_tweet_id
            ON symbol_tweets(tweet_id);
            """
        )

    @staticmethod
    def _timestamp(value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _payload(tweet: TweetItem) -> str:
        return json.dumps(
            tweet.model_dump(mode="json", by_alias=True, exclude_none=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def upsert_symbol_tweets(
        self,
        symbol: str,
        tweets: list[TweetItem],
        *,
        observed_at: datetime | None = None,
    ) -> StoreResult:
        now = self._timestamp(observed_at or datetime.now(UTC))
        new_for_symbol = 0
        globally_new = 0
        updated = 0
        unchanged = 0

        # The API occasionally repeats the page boundary. Keep the first (newest)
        # occurrence and make one deterministic write per tweet id.
        unique: dict[str, TweetItem] = {}
        for tweet in tweets:
            unique.setdefault(tweet.id, tweet)

        with self.connection:
            for tweet in unique.values():
                payload = self._payload(tweet)
                existing = self.connection.execute(
                    "SELECT payload FROM tweets WHERE id = ?", (tweet.id,)
                ).fetchone()
                if existing is None:
                    self.connection.execute(
                        """
                        INSERT INTO tweets
                            (id, send_time, payload, first_seen_at, last_seen_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tweet.id,
                            self._timestamp(tweet.send_time),
                            payload,
                            now,
                            now,
                            now,
                        ),
                    )
                    globally_new += 1
                elif existing[0] != payload:
                    self.connection.execute(
                        """
                        UPDATE tweets
                        SET send_time = ?, payload = ?, last_seen_at = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            self._timestamp(tweet.send_time),
                            payload,
                            now,
                            now,
                            tweet.id,
                        ),
                    )
                    updated += 1
                else:
                    self.connection.execute(
                        "UPDATE tweets SET last_seen_at = ? WHERE id = ?",
                        (now, tweet.id),
                    )
                    unchanged += 1

                inserted = self.connection.execute(
                    """
                    INSERT OR IGNORE INTO symbol_tweets
                        (symbol, tweet_id, first_seen_at, last_seen_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (symbol, tweet.id, now, now),
                )
                if inserted.rowcount == 1:
                    new_for_symbol += 1
                else:
                    self.connection.execute(
                        """
                        UPDATE symbol_tweets SET last_seen_at = ?
                        WHERE symbol = ? AND tweet_id = ?
                        """,
                        (now, symbol, tweet.id),
                    )

        return StoreResult(
            fetched_count=len(unique),
            new_for_symbol_count=new_for_symbol,
            globally_new_count=globally_new,
            updated_count=updated,
            unchanged_count=unchanged,
        )

    def get_tweet(self, tweet_id: str) -> TweetItem | None:
        row = self.connection.execute(
            "SELECT payload FROM tweets WHERE id = ?", (str(tweet_id),)
        ).fetchone()
        if row is None:
            return None
        return TweetItem.model_validate_json(row[0])

    def close(self) -> None:
        try:
            # Artifacts persist only the main database file. Force WAL contents
            # into it before the GitHub Actions upload step.
            self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            self.connection.close()

    def __enter__(self) -> SqliteTweetStore:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
