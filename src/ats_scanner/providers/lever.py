"""Lever provider — hits the public postings endpoint.

Port of career-ops's providers/lever.mjs. Auto-detects from a
`https://jobs.lever.co/<slug>` careers_url.

API shape:
    GET https://api.lever.co/v0/postings/<slug>
    -> [ { "text", "hostedUrl", "categories": {"location"},
           "descriptionPlain", "createdAt" (epoch ms) } ]

Lever ships the full description in the list payload for free (no per-job request).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from ..http import HttpClient
from ..models import Job, WatchlistEntry
from .base import assert_allowed_host

ALLOWED_HOSTS = {"api.lever.co", "jobs.lever.co"}

_SLUG_RE = re.compile(r"jobs\.lever\.co/([^/?#]+)")


def _resolve_api_url(entry: WatchlistEntry) -> str | None:
    match = _SLUG_RE.search(entry.careers_url or "")
    if not match:
        return None
    return f"https://api.lever.co/v0/postings/{match.group(1)}"


def _parse_epoch_ms(value: object) -> datetime | None:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    return None


class LeverProvider:
    id = "lever"

    def detect(self, entry: WatchlistEntry) -> str | None:
        return _resolve_api_url(entry)

    def fetch(self, entry: WatchlistEntry, http: HttpClient) -> list[Job]:
        api_url = _resolve_api_url(entry)
        if not api_url:
            raise ValueError(f"lever: cannot derive API URL for {entry.name}")
        assert_allowed_host(api_url, ALLOWED_HOSTS)
        data = http.get_json(api_url)
        if not isinstance(data, list):
            return []
        jobs: list[Job] = []
        for j in data:
            url = j.get("hostedUrl", "") or ""
            if not url:
                continue
            location = (j.get("categories") or {}).get("location", "") or ""
            description = j.get("descriptionPlain", "")
            jobs.append(
                Job(
                    title=j.get("text", "") or "",
                    url=url,
                    company=entry.name,
                    location=location,
                    description=description if isinstance(description, str) else "",
                    posted_at=_parse_epoch_ms(j.get("createdAt")),
                )
            )
        return jobs
