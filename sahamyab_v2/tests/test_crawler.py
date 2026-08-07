from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sahamyab_v2.crawler import IncompleteCrawlError, SahamyabCrawler
from sahamyab_v2.state import SymbolRegistry
from sahamyab_v2.storage import SqliteTweetStore
from sahamyab_v2.tests.test_models import tweet_payload


class FakeClient:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages
        self.payloads: list[dict[str, Any]] = []

    def post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(payload)
        return self.pages[len(self.payloads) - 1]


class CrawlerTests(unittest.TestCase):
    def test_reads_every_page_updates_old_tweets_and_counts_only_new_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            symbols_file = root / "symbols.json"
            symbols_file.write_text('{"فولاد":{}}', encoding="utf-8")
            registry = SymbolRegistry(symbols_file)

            first_client = FakeClient(
                [
                    {
                        "items": [tweet_payload("2", "1")],
                        "hasMore": True,
                    },
                    {
                        "items": [tweet_payload("1", "1")],
                        "hasMore": False,
                    },
                ]
            )
            database = root / "tweets.sqlite3"
            run_at = datetime(2026, 8, 6, 10, tzinfo=UTC)

            with SqliteTweetStore(database) as store:
                first = SahamyabCrawler(
                    first_client, store, registry, page_delay=0
                ).crawl_symbol("فولاد", run_at=run_at)
                self.assertEqual(first.page_count, 2)
                self.assertEqual(first.store.new_for_symbol_count, 2)
                self.assertEqual(first_client.payloads[1]["id"], "2")

                second_client = FakeClient(
                    [
                        {
                            "items": [
                                tweet_payload("2", "9"),
                                tweet_payload("1", "1"),
                            ],
                            "hasMore": False,
                        }
                    ]
                )
                second = SahamyabCrawler(
                    second_client, store, registry, page_delay=0
                ).crawl_symbol("فولاد", run_at=run_at)

                self.assertEqual(second.store.new_for_symbol_count, 0)
                self.assertEqual(second.store.updated_count, 1)
                self.assertEqual(store.get_tweet("2").like_count, 9)

            state = json.loads(symbols_file.read_text(encoding="utf-8"))
            self.assertEqual(state["فولاد"]["last_run_tweet_count"], 0)
            self.assertIn("بازار_سرمایه", state)

    def test_does_not_write_partial_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            symbols_file = root / "symbols.json"
            symbols_file.write_text('{"فولاد":{}}', encoding="utf-8")
            registry = SymbolRegistry(symbols_file)
            client = FakeClient(
                [{"items": [tweet_payload("1")], "hasMore": True}]
            )

            with SqliteTweetStore(root / "tweets.sqlite3") as store:
                crawler = SahamyabCrawler(
                    client, store, registry, page_delay=0, max_pages=1
                )
                with self.assertRaises(IncompleteCrawlError):
                    crawler.crawl_symbol("فولاد")
                self.assertIsNone(store.get_tweet("1"))


if __name__ == "__main__":
    unittest.main()
