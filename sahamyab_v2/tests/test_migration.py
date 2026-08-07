from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sahamyab_v2.migration import import_legacy_snapshots
from sahamyab_v2.storage import SqliteTweetStore
from sahamyab_v2.tests.test_models import tweet_payload


class MigrationTests(unittest.TestCase):
    def test_legacy_import_is_idempotent_and_discovers_hashtags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshots = root / "snapshots"
            snapshots.mkdir()
            snapshot = snapshots / "20260806_فولاد.json"
            snapshot.write_text(
                json.dumps(tweet_payload("101"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            symbols = root / "symbols.json"
            symbols.write_text('{"فولاد":{}}', encoding="utf-8")
            database = root / "tweets.sqlite3"

            first = import_legacy_snapshots(
                snapshot_root=snapshots,
                database_file=database,
                symbols_file=symbols,
            )
            second = import_legacy_snapshots(
                snapshot_root=snapshots,
                database_file=database,
                symbols_file=symbols,
            )

            self.assertEqual(first.associations, 3)
            self.assertEqual(second.associations, 0)
            saved_symbols = json.loads(symbols.read_text(encoding="utf-8"))
            self.assertIn("بازار_سرمایه", saved_symbols)
            with SqliteTweetStore(database) as store:
                self.assertEqual(store.get_tweet("101").sender_username, "user")


if __name__ == "__main__":
    unittest.main()
