"""The orchestrator — ties providers, filters, and history together.

For each enabled company: route to a provider, fetch, filter by title then location,
drop URLs already in history. A failure on one board is logged and skipped so it never
aborts the whole run (career-ops's per-company isolation).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .filters import apply_location_filter, apply_title_filter
from .history import ScanHistory
from .http import HttpClient
from .models import Job, Watchlist
from .providers import route

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    new_jobs: list[Job] = field(default_factory=list)
    # Everything passing the filters, before the history check. `new_jobs` is the
    # subset not seen before; priming needs the whole set.
    matched_jobs: list[Job] = field(default_factory=list)
    companies_scanned: int = 0
    total_fetched: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)  # (company, message)


def run_scan(watchlist: Watchlist, http: HttpClient, history: ScanHistory) -> ScanResult:
    result = ScanResult()
    for entry in watchlist.tracked_companies:
        if not entry.enabled:
            continue
        provider = route(entry)
        if provider is None:
            msg = f"no provider matched careers_url: {entry.careers_url!r}"
            logger.warning("%s: %s", entry.name, msg)
            result.errors.append((entry.name, msg))
            continue

        try:
            jobs = provider.fetch(entry, http)
        except Exception as exc:  # one bad board must not abort the run
            logger.warning("%s: fetch failed (%s): %s", entry.name, provider.id, exc)
            result.errors.append((entry.name, str(exc)))
            continue

        result.companies_scanned += 1
        result.total_fetched += len(jobs)

        jobs = apply_title_filter(jobs, watchlist.title_filter)
        jobs = apply_location_filter(jobs, watchlist.location_filter)
        result.matched_jobs.extend(jobs)
        new_jobs = [j for j in jobs if not history.is_seen(j.url)]
        result.new_jobs.extend(new_jobs)

    return result
