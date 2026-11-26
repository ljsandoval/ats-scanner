"""Provider contract + shared host-allowlist guard.

A Provider is one module per ATS. It answers two questions:
  - detect(entry): can I handle this company? -> the API URL, or None
  - fetch(entry, http): give me the jobs -> list[Job]

`assert_allowed_host` is the security check ported from career-ops's
`assertGreenhouseUrl`: every derived API URL must be HTTPS and its hostname must be
on the provider's own allowlist. Combined with http.py's redirect refusal, this
guarantees we only ever talk to hosts we validated.
"""

from __future__ import annotations

from typing import Protocol
from urllib.parse import urlparse

from ..http import HttpClient
from ..models import Job, WatchlistEntry


class Provider(Protocol):
    id: str

    def detect(self, entry: WatchlistEntry) -> str | None:
        """Return the API URL if this provider handles the entry, else None."""
        ...

    def fetch(self, entry: WatchlistEntry, http: HttpClient) -> list[Job]:
        """Fetch and normalize the company's postings."""
        ...


def assert_allowed_host(url: str, allowed: set[str]) -> str:
    """Validate that url is HTTPS and its hostname is in the allowlist.

    Returns the url unchanged so it can be used inline. Raises ValueError otherwise.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"URL must use HTTPS: {url}")
    if parsed.hostname not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(
            f'untrusted hostname "{parsed.hostname}" — must be one of: {allowed_list}'
        )
    return url
