from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from .hashtags import HashtagExtractor
from .models import TweetItem
from .state import SymbolRegistry
from .storage import SqliteTweetStore


LOGGER = logging.getLogger("sahamyab_v2.migration")
SYMBOL_FILENAME = re.compile(r"^\d{8}_(.+)\.json$")


@dataclass(frozen=True, slots=True)
class MigrationSummary:
    files: int
    valid_records: int
    invalid_records: int
    associations: int
    discovered_hashtags: int


def import_legacy_snapshots(
    *,
    snapshot_root: str | Path,
    database_file: str | Path,
    symbols_file: str | Path,
) -> MigrationSummary:
    """Idempotently imports old JSONL snapshots into the new canonical store."""

    root = Path(snapshot_root)
    registry = SymbolRegistry(symbols_file)
    extractor = HashtagExtractor()
    file_count = valid = invalid = associations = 0
    all_hashtags: set[str] = set()
    observed_at = datetime.now(UTC)

    with SqliteTweetStore(database_file) as store:
        for path in sorted(root.rglob("*.json")):
            file_count += 1
            match = SYMBOL_FILENAME.match(path.name)
            filename_symbol = match.group(1) if match else None
            grouped: dict[str, list[TweetItem]] = {}

            with path.open("r", encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, start=1):
                    if not line.strip():
                        continue
                    try:
                        raw = json.loads(line)
                        tweet = TweetItem.model_validate(raw)
                    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
                        invalid += 1
                        LOGGER.warning("invalid record %s:%s: %s", path, line_number, exc)
                        continue

                    valid += 1
                    hashtags = extractor.extract_tweet(tweet)
                    all_hashtags.update(hashtags)
                    # A per-symbol snapshot proves the filename association, while
                    # the tweet text can prove additional hashtag associations.
                    targets = set(hashtags)
                    if filename_symbol:
                        targets.add(filename_symbol)
                    for symbol in targets:
                        if symbol:
                            grouped.setdefault(symbol, []).append(tweet)

            for symbol, tweets in grouped.items():
                result = store.upsert_symbol_tweets(
                    symbol,
                    tweets,
                    observed_at=observed_at,
                )
                associations += result.new_for_symbol_count

    discovered = registry.add_hashtags(all_hashtags, observed_at.date())
    if discovered:
        registry.save()
    return MigrationSummary(
        files=file_count,
        valid_records=valid,
        invalid_records=invalid,
        associations=associations,
        discovered_hashtags=discovered,
    )
