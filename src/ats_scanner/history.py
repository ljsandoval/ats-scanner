"""Scan history — the dedup ledger.

A TSV of URLs the scanner has already reported, so the next run does not surface them
again. This is internal STATE, not output: it stays beside the tool and is never
written to the vault. Ported from career-ops's loadSeenUrls / appendToScanHistory.

Columns: url \t status \t first_seen (ISO date). We dedup on column 0, so extra
columns can be added later without breaking old files.
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

from .models import Job

_COLUMNS = ("url", "status", "first_seen")


class ScanHistory:
    def __init__(self, path: str | Path, *, recheck_after_days: int | None = None) -> None:
        self.path = Path(path)
        self.recheck_after_days = recheck_after_days
        self._seen: dict[str, date] = self._load()

    def _load(self) -> dict[str, date]:
        seen: dict[str, date] = {}
        if not self.path.exists():
            return seen
        with open(self.path, newline="") as f:
            for row in csv.reader(f, delimiter="\t"):
                if not row or not row[0] or row[0] == _COLUMNS[0]:
                    continue  # skip blanks and the header row
                url = row[0]
                first_seen = _parse_date(row[2]) if len(row) > 2 else None
                seen[url] = first_seen or date.min
        return seen

    def is_seen(self, url: str) -> bool:
        """True if we should skip this URL (already reported and not yet re-eligible)."""
        if url not in self._seen:
            return False
        if self.recheck_after_days is None:
            return True
        age = date.today() - self._seen[url]
        # Older than the recheck window -> treat as unseen again (role may have reopened).
        return age < timedelta(days=self.recheck_after_days)

    def record(self, jobs: list[Job], *, status: str = "active") -> int:
        """Append newly seen job URLs to the TSV. Returns how many were added."""
        today = date.today().isoformat()
        new_rows = []
        for job in jobs:
            if job.url not in self._seen:
                new_rows.append((job.url, status, today))
                self._seen[job.url] = date.today()
        if not new_rows:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists()
        with open(self.path, "a", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            if write_header:
                writer.writerow(_COLUMNS)
            writer.writerows(new_rows)
        return len(new_rows)


def _parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value).date()
    except (ValueError, TypeError):
        return None
