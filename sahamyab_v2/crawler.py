from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from .hashtags import HashtagExtractor
from .models import TweetItem, TweetPage
from .state import SymbolRegistry
from .storage import SqliteTweetStore, StoreResult


SAHAMYAB_URL = "https://www.sahamyab.com/guest/twiter/list?v=0.1"


class JsonClient(Protocol):
    def post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class IncompleteCrawlError(RuntimeError):
    """Raised when pagination cannot safely reach the last available page."""


@dataclass(frozen=True, slots=True)
class CrawlResult:
    symbol: str
    page_count: int
    discovered_hashtag_count: int
    newest_id: str | None
    store: StoreResult


class SahamyabCrawler:
    def __init__(
        self,
        client: JsonClient,
        store: SqliteTweetStore,
        registry: SymbolRegistry,
        *,
        url: str = SAHAMYAB_URL,
        page_delay: float = 0.5,
        max_pages: int | None = None,
    ) -> None:
        self.client = client
        self.store = store
        self.registry = registry
        self.url = url
        self.page_delay = max(0.0, page_delay)
        self.max_pages = max_pages if max_pages and max_pages > 0 else None
        self.hashtags = HashtagExtractor()

    def fetch_all(self, symbol: str) -> tuple[list[TweetItem], int]:
        page_number = 0
        next_id: str | None = None
        seen_cursors: set[str] = set()
        unique: dict[str, TweetItem] = {}

        while True:
            payload: dict[str, Any] = {"page": page_number, "tag": symbol}
            if next_id is not None:
                payload["id"] = next_id

            page = TweetPage.model_validate(self.client.post_json(self.url, payload))
            for tweet in page.items:
                unique.setdefault(tweet.id, tweet)

            page_number += 1
            if not page.has_more:
                break
            if not page.items:
                raise IncompleteCrawlError(
                    f"hasMore=true but page {page_number - 1} is empty for {symbol!r}"
                )
            if self.max_pages is not None and page_number >= self.max_pages:
                raise IncompleteCrawlError(
                    f"max_pages={self.max_pages} reached before the last page for {symbol!r}"
                )

            cursor = page.items[-1].id
            if cursor in seen_cursors:
                raise IncompleteCrawlError(
                    f"repeated pagination cursor {cursor!r} for {symbol!r}"
                )
            seen_cursors.add(cursor)
            next_id = cursor
            if self.page_delay:
                time.sleep(self.page_delay)

        return list(unique.values()), page_number

    def crawl_symbol(
        self, symbol: str, *, run_at: datetime | None = None
    ) -> CrawlResult:
        observed_at = run_at or datetime.now(UTC)
        tweets, page_count = self.fetch_all(symbol)

        # No persistent state changes occur before complete pagination succeeds.
        store_result = self.store.upsert_symbol_tweets(
            symbol,
            tweets,
            observed_at=observed_at,
        )
        discovered = self.hashtags.extract_many(tweets)
        added_count = self.registry.add_hashtags(discovered, observed_at.date())
        newest_id = tweets[0].id if tweets else None
        self.registry.mark_success(
            symbol,
            run_at=observed_at,
            new_tweet_count=store_result.new_for_symbol_count,
            newest_id=newest_id,
        )
        self.registry.save()

        return CrawlResult(
            symbol=symbol,
            page_count=page_count,
            discovered_hashtag_count=added_count,
            newest_id=newest_id,
            store=store_result,
        )
