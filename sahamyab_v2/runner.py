from __future__ import annotations

import logging
import math
import os
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Protocol

from requests import HTTPError

from .crawler import CrawlResult, SahamyabCrawler
from .http_client import HttpClient
from .state import SymbolRegistry
from .storage import SqliteTweetStore


LOGGER = logging.getLogger("sahamyab_v2")
THROTTLE_STATUS_CODES = frozenset((403, 429))


class SymbolCrawler(Protocol):
    def crawl_symbol(
        self, symbol: str, *, run_at: datetime | None = None
    ) -> CrawlResult: ...


class AdaptiveWait:
    """Exponential throttling delay with bounded random jitter.

    A 403/429 raises the pressure level. Each successful symbol lowers it by
    one level, so the crawler returns to its normal speed gradually.
    """

    def __init__(
        self,
        *,
        base_delay: float = 15.0,
        max_delay: float = 300.0,
        jitter_ratio: float = 0.25,
        random_uniform: Callable[[float, float], float] = random.uniform,
    ) -> None:
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay cannot be smaller than base_delay")
        if not 0 <= jitter_ratio <= 1:
            raise ValueError("jitter_ratio must be between 0 and 1")
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_ratio = jitter_ratio
        self.random_uniform = random_uniform
        self.pressure_level = 0

    def record_throttle(self) -> None:
        self.pressure_level += 1

    def record_success(self) -> None:
        self.pressure_level = max(0, self.pressure_level - 1)

    def delay(self, normal_delay: float) -> float:
        normal = max(0.0, normal_delay)
        if self.pressure_level == 0:
            return normal

        max_exponent = max(
            0,
            math.ceil(math.log2(self.max_delay / self.base_delay)),
        )
        exponent = min(self.pressure_level - 1, max_exponent)
        exponential = self.base_delay * (2**exponent)
        jitter = self.random_uniform(
            1.0 - self.jitter_ratio,
            1.0 + self.jitter_ratio,
        )
        adaptive = min(self.max_delay, exponential * jitter)
        return max(normal, adaptive)


def is_throttle_error(error: Exception) -> bool:
    return (
        isinstance(error, HTTPError)
        and error.response is not None
        and error.response.status_code in THROTTLE_STATUS_CODES
    )


class SingleRunLock:
    """Cross-platform advisory lock preventing concurrent crawler runs."""

    def __init__(self, filename: str | Path) -> None:
        self.filename = Path(filename)
        self.stream = None

    def __enter__(self) -> SingleRunLock:
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.filename.open("a+")
        self.stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                if self.filename.stat().st_size == 0:
                    self.stream.write("0")
                    self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            self.stream.close()
            raise RuntimeError("another Sahamyab crawler is already running") from exc
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.stream is None:
            return
        try:
            self.stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        finally:
            self.stream.close()


@dataclass(frozen=True, slots=True)
class RunSummary:
    attempted_symbols: int
    request_attempts: int
    retried_symbols: int
    recovered_symbols: int
    successful_symbols: int
    failed_symbols: int
    fetched_tweets: int
    new_tweets: int
    updated_tweets: int
    discovered_hashtags: int


def run_batch(
    *,
    crawler: SymbolCrawler,
    registry: SymbolRegistry,
    symbols: list[str],
    symbol_delay: float,
    adaptive_wait: AdaptiveWait,
    sleeper: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> RunSummary:
    """Run selected symbols and append each failed symbol once to batch end."""

    successful = final_failed = fetched = new = updated = discovered = 0
    request_attempts = retried = recovered = 0
    work: list[tuple[str, int]] = [(symbol, 1) for symbol in symbols]
    index = 0

    while index < len(work):
        symbol, attempt = work[index]
        index += 1
        request_attempts += 1
        run_at = now()
        try:
            result = crawler.crawl_symbol(symbol, run_at=run_at)
            adaptive_wait.record_success()
            successful += 1
            if attempt == 2:
                recovered += 1
            fetched += result.store.fetched_count
            new += result.store.new_for_symbol_count
            updated += result.store.updated_count
            discovered += result.discovered_hashtag_count
            LOGGER.info(
                "[%s/%s] %s attempt=%s pages=%s fetched=%s new=%s "
                "updated=%s hashtags=%s",
                index,
                len(work),
                symbol,
                attempt,
                result.page_count,
                result.store.fetched_count,
                result.store.new_for_symbol_count,
                result.store.updated_count,
                result.discovered_hashtag_count,
            )
        except Exception as exc:
            throttled = is_throttle_error(exc)
            if throttled:
                adaptive_wait.record_throttle()
            registry.mark_failure(symbol, run_at=run_at, error=str(exc))
            registry.save()

            if attempt == 1:
                work.append((symbol, 2))
                retried += 1
                LOGGER.exception(
                    "[%s/%s] failed symbol=%s attempt=1; queued once at batch end",
                    index,
                    len(work),
                    symbol,
                )
            else:
                final_failed += 1
                LOGGER.exception(
                    "[%s/%s] failed symbol=%s attempt=2; no more retries",
                    index,
                    len(work),
                    symbol,
                )

        if index < len(work):
            delay = adaptive_wait.delay(symbol_delay)
            LOGGER.info(
                "waiting %.2fs before next symbol (pressure_level=%s)",
                delay,
                adaptive_wait.pressure_level,
            )
            if delay:
                sleeper(delay)

    return RunSummary(
        attempted_symbols=len(symbols),
        request_attempts=request_attempts,
        retried_symbols=retried,
        recovered_symbols=recovered,
        successful_symbols=successful,
        failed_symbols=final_failed,
        fetched_tweets=fetched,
        new_tweets=new,
        updated_tweets=updated,
        discovered_hashtags=discovered,
    )


def run(
    *,
    symbols_file: str | Path,
    database_file: str | Path,
    limit: int = 150,
    page_delay: float = 0.5,
    symbol_delay: float = 1.0,
    max_pages: int | None = None,
    timeout: float = 30,
    backoff_base: float = 15.0,
    backoff_max: float = 300.0,
    backoff_jitter: float = 0.25,
) -> RunSummary:
    registry = SymbolRegistry(symbols_file)
    symbols = registry.prioritized_symbols(limit)
    lock_file = Path(database_file).with_suffix(".lock")

    with SingleRunLock(lock_file), HttpClient(timeout=timeout) as client, SqliteTweetStore(
        database_file
    ) as store:
        crawler = SahamyabCrawler(
            client,
            store,
            registry,
            page_delay=page_delay,
            max_pages=max_pages,
        )
        return run_batch(
            crawler=crawler,
            registry=registry,
            symbols=symbols,
            symbol_delay=symbol_delay,
            adaptive_wait=AdaptiveWait(
                base_delay=backoff_base,
                max_delay=backoff_max,
                jitter_ratio=backoff_jitter,
            ),
        )
