from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from sahamyab_v2.state import SymbolRegistry


class SymbolRegistryTests(unittest.TestCase):
    def test_prioritizes_oldest_then_highest_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "symbols.json"
            path.write_text(
                json.dumps(
                    {
                        "جدید": {"last_run_at": "2026-08-06T10:00:00Z"},
                        "کم": {
                            "last_run_at": "2026-08-01T10:00:00Z",
                            "last_run_tweet_count": 2,
                        },
                        "زیاد": {
                            "last_run_at": "2026-08-01T10:00:00Z",
                            "last_run_tweet_count": 20,
                        },
                        "هرگز": {},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            registry = SymbolRegistry(path)

            self.assertEqual(
                registry.prioritized_symbols(), ["هرگز", "زیاد", "کم", "جدید"]
            )

    def test_add_hashtags_never_removes_or_overwrites_existing_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "symbols.json"
            path.write_text(
                '{"فولاد":{"custom":"keep","first_seen":"2020-01-01"}}',
                encoding="utf-8",
            )
            registry = SymbolRegistry(path)

            added = registry.add_hashtags(
                {"فولاد", "خودرو"}, datetime(2026, 8, 6, tzinfo=UTC).date()
            )
            registry.save()
            saved = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(added, 1)
            self.assertEqual(saved["فولاد"]["custom"], "keep")
            self.assertIn("خودرو", saved)


if __name__ == "__main__":
    unittest.main()
