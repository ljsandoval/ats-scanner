"""Greenhouse provider — hits the public boards-api JSON endpoint.

Port of career-ops's providers/greenhouse.mjs. Handles both an explicit `api:` URL
and auto-detection from `careers_url`.

API shape:
    GET https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
    -> { "jobs": [ { "title", "absolute_url", "location": {"name"}, "first_published" } ] }
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from ..http import HttpClient
from ..models import Job, WatchlistEntry
from .base import assert_allowed_host

ALLOWED_HOSTS = {
    "boards-api.greenhouse.io",
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "job-boards.eu.greenhouse.io",
}

_SLUG_RE = re.compile(r"job-boards(?:\.eu)?\.greenhouse\.io/([^/?#]+)")


def _resolve_api_url(entry: WatchlistEntry) -> str | None:
    if entry.api:
        return assert_allowed_host(entry.api, ALLOWED_HOSTS)
    match = _SLUG_RE.search(entry.careers_url or "")
    if match:
        return f"https://boards-api.greenhouse.io/v1/boards/{match.group(1)}/jobs"
    return None


def _parse_date(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class GreenhouseProvider:
    id = "greenhouse"

    def detect(self, entry: WatchlistEntry) -> str | None:
        try:
            return _resolve_api_url(entry)
        except ValueError:
            return None

    def fetch(self, entry: WatchlistEntry, http: HttpClient) -> list[Job]:
        api_url = _resolve_api_url(entry)
        if not api_url:
            raise ValueError(f"greenhouse: cannot derive API URL for {entry.name}")
        assert_allowed_host(api_url, ALLOWED_HOSTS)
        data = http.get_json(api_url)
        jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
        jobs: list[Job] = []
        for j in jobs_raw:
            url = j.get("absolute_url")
            if not url:
                continue
            location = (j.get("location") or {}).get("name", "") or ""
            jobs.append(
                Job(
                    title=j.get("title", "") or "",
                    url=url,
                    company=entry.name,
                    location=location,
                    posted_at=_parse_date(j.get("first_published")),
                )
            )
        return jobs
