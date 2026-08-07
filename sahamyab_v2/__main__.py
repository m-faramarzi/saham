from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .migration import import_legacy_snapshots
from .runner import run


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Idempotent Sahamyab crawler")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    crawl = commands.add_parser("crawl", help="crawl prioritized hashtags")
    crawl.add_argument("--symbols-file", type=Path, default=PROJECT_ROOT / "symbols.json")
    crawl.add_argument(
        "--database", type=Path, default=PACKAGE_ROOT / "data" / "sahamyab.sqlite3"
    )
    crawl.add_argument(
        "--limit",
        type=int,
        default=150,
        help="number of prioritized hashtags; 0 means all",
    )
    crawl.add_argument("--page-delay", type=float, default=0.5)
    crawl.add_argument("--symbol-delay", type=float, default=1.0)
    crawl.add_argument(
        "--backoff-base",
        type=float,
        default=15,
        help="initial wait after a 403/429 response",
    )
    crawl.add_argument(
        "--backoff-max",
        type=float,
        default=300,
        help="maximum adaptive wait between symbols",
    )
    crawl.add_argument(
        "--backoff-jitter",
        type=float,
        default=0.25,
        help="random jitter ratio between 0 and 1",
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="safety limit; 0 reads until hasMore=false",
    )
    crawl.add_argument("--timeout", type=float, default=30)

    migrate = commands.add_parser(
        "import-legacy", help="idempotently import existing JSONL snapshots"
    )
    migrate.add_argument("--snapshots", type=Path, default=PROJECT_ROOT / "snapshots")
    migrate.add_argument("--symbols-file", type=Path, default=PROJECT_ROOT / "symbols.json")
    migrate.add_argument(
        "--database", type=Path, default=PACKAGE_ROOT / "data" / "sahamyab.sqlite3"
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.command == "crawl":
        summary = run(
            symbols_file=args.symbols_file,
            database_file=args.database,
            limit=args.limit,
            page_delay=args.page_delay,
            symbol_delay=args.symbol_delay,
            max_pages=args.max_pages,
            timeout=args.timeout,
            backoff_base=args.backoff_base,
            backoff_max=args.backoff_max,
            backoff_jitter=args.backoff_jitter,
        )
    else:
        summary = import_legacy_snapshots(
            snapshot_root=args.snapshots,
            database_file=args.database,
            symbols_file=args.symbols_file,
        )
    print(summary)


if __name__ == "__main__":
    main()
