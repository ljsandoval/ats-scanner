"""Command-line entry point: `ats-scanner scan` (or `python -m ats_scanner scan`)."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

from .config import load_watchlist
from .history import ScanHistory
from .http import HttpClient
from .output import write_outputs
from .scanner import run_scan


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ats-scanner",
        description="Zero-token watchlist job scanner (Greenhouse, Lever).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan the watchlist for new postings.")
    scan.add_argument("--config", default="config/watchlist.yaml", help="watchlist YAML path")
    scan.add_argument("--out", default="./output", help="output directory")
    scan.add_argument("--history", default="./data/scan-history.tsv", help="dedup TSV path")
    scan.add_argument("--no-md", action="store_true", help="skip markdown output")
    scan.add_argument("--no-json", action="store_true", help="skip JSON output")
    scan.add_argument(
        "--dry-run", action="store_true", help="scan and print counts; write nothing"
    )
    scan.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    return parser


def _run_scan(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        watchlist = load_watchlist(args.config)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    history = ScanHistory(
        args.history, recheck_after_days=watchlist.scan_history.recheck_after_days
    )
    run_dt = datetime.now()

    with HttpClient() as http:
        result = run_scan(watchlist, http, history)

    summary = (
        f"{len(result.new_jobs)} new / {result.total_fetched} fetched "
        f"across {result.companies_scanned} company(ies)"
    )
    if result.errors:
        summary += f" ({len(result.errors)} error(s))"

    if args.dry_run:
        print(f"[dry-run] {summary} — nothing written")
        for job in result.new_jobs:
            print(f"  - {job.company}: {job.title} ({job.location or 'n/a'})")
        return 0

    written = write_outputs(
        result.new_jobs,
        args.out,
        run_dt=run_dt,
        md=not args.no_md,
        json_=not args.no_json,
    )
    # Record only after a successful write, so a failed run does not hide roles next time.
    history.record(result.new_jobs)

    print(summary)
    for path in written:
        print(f"  wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "scan":
        return _run_scan(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
