from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from requests import HTTPError, Response

from sahamyab_v2.crawler import CrawlResult
from sahamyab_v2.runner import AdaptiveWait, run_batch
from sahamyab_v2.state import SymbolRegistry
from sahamyab_v2.storage import StoreResult


def successful_result(symbol: str) -> CrawlResult:
    return CrawlResult(
        symbol=symbol,
        page_count=1,
        discovered_hashtag_count=0,
        newest_id="1",
        store=StoreResult(
            fetched_count=1,
            new_for_symbol_count=1,
            globally_new_count=1,
            updated_count=0,
            unchanged_count=0,
        ),
    )


def http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    response.url = "https://www.sahamyab.com/guest/twiter/list?v=0.1"
    return HTTPError(f"status={status_code}", response=response)


class ScriptedCrawler:
    def __init__(self, script: dict[str, list[Exception | CrawlResult]]) -> None:
        self.script = script
        self.calls: list[str] = []

    def crawl_symbol(
        self, symbol: str, *, run_at: datetime | None = None
    ) -> CrawlResult:
        self.calls.append(symbol)
        outcome = self.script[symbol].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class AdaptiveWaitTests(unittest.TestCase):
    def test_exponential_wait_has_jitter_cap_and_gradual_recovery(self) -> None:
        wait = AdaptiveWait(
            base_delay=10,
            max_delay=25,
            jitter_ratio=0,
        )

        wait.record_throttle()
        self.assertEqual(wait.delay(1), 10)
        wait.record_throttle()
        self.assertEqual(wait.delay(1), 20)
        wait.record_throttle()
        self.assertEqual(wait.delay(1), 25)
        wait.record_success()
        self.assertEqual(wait.delay(1), 20)

    def test_jitter_never_exceeds_maximum(self) -> None:
        wait = AdaptiveWait(
            base_delay=20,
            max_delay=30,
            jitter_ratio=0.5,
            random_uniform=lambda lower, upper: upper,
        )
        wait.record_throttle()
        wait.record_throttle()

        self.assertEqual(wait.delay(1), 30)


class BatchRetryTests(unittest.TestCase):
    def test_failed_symbol_is_retried_once_at_batch_end_and_can_recover(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            symbols_file = Path(temporary) / "symbols.json"
            symbols_file.write_text('{"الف":{},"ب":{}}', encoding="utf-8")
            registry = SymbolRegistry(symbols_file)
            crawler = ScriptedCrawler(
                {
                    "الف": [http_error(403), successful_result("الف")],
                    "ب": [successful_result("ب")],
                }
            )
            sleeps: list[float] = []

            summary = run_batch(
                crawler=crawler,
                registry=registry,
                symbols=["الف", "ب"],
                symbol_delay=1,
                adaptive_wait=AdaptiveWait(
                    base_delay=10,
                    max_delay=60,
                    jitter_ratio=0,
                ),
                sleeper=sleeps.append,
                now=lambda: datetime(2026, 8, 7, tzinfo=UTC),
            )

            self.assertEqual(crawler.calls, ["الف", "ب", "الف"])
            self.assertEqual(sleeps, [10, 1])
            self.assertEqual(summary.request_attempts, 3)
            self.assertEqual(summary.retried_symbols, 1)
            self.assertEqual(summary.recovered_symbols, 1)
            self.assertEqual(summary.successful_symbols, 2)
            self.assertEqual(summary.failed_symbols, 0)

    def test_second_failure_is_not_queued_again(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            symbols_file = Path(temporary) / "symbols.json"
            symbols_file.write_text('{"الف":{}}', encoding="utf-8")
            registry = SymbolRegistry(symbols_file)
            crawler = ScriptedCrawler(
                {"الف": [http_error(403), http_error(403)]}
            )

            summary = run_batch(
                crawler=crawler,
                registry=registry,
                symbols=["الف"],
                symbol_delay=0,
                adaptive_wait=AdaptiveWait(
                    base_delay=1,
                    max_delay=2,
                    jitter_ratio=0,
                ),
                sleeper=lambda delay: None,
                now=lambda: datetime(2026, 8, 7, tzinfo=UTC),
            )

            self.assertEqual(crawler.calls, ["الف", "الف"])
            self.assertEqual(summary.request_attempts, 2)
            self.assertEqual(summary.retried_symbols, 1)
            self.assertEqual(summary.recovered_symbols, 0)
            self.assertEqual(summary.successful_symbols, 0)
            self.assertEqual(summary.failed_symbols, 1)


if __name__ == "__main__":
    unittest.main()
