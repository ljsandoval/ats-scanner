"""HTTP transport — a thin wrapper over httpx.

Ports career-ops's `providers/_http.mjs`. The one security-relevant detail is
`follow_redirects=False`: providers validate a URL's hostname against an allowlist
before fetching, so we must NOT let a server-side 3xx redirect bounce us to an
un-validated host (an SSRF vector). Node's equivalent is `redirect: 'error'`.
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_TIMEOUT_S = 10.0
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; ats-scanner/0.1)"


class RedirectNotAllowed(Exception):
    """Raised when a request returns a 3xx — we surface redirects, never follow them."""


class HttpClient:
    """Minimal JSON HTTP client with a redirect guard.

    Usable as a context manager so the underlying connection pool is closed cleanly.
    """

    def __init__(
        self,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._client = httpx.Client(
            timeout=timeout_s,
            headers={"user-agent": user_agent, "accept": "application/json"},
            follow_redirects=False,  # SSRF guard — see module docstring
        )

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get_json(self, url: str) -> Any:
        """GET a URL and parse JSON.

        Raises RedirectNotAllowed on any 3xx, and httpx.HTTPStatusError on 4xx/5xx.
        """
        resp = self._client.get(url)
        if resp.is_redirect:
            location = resp.headers.get("location", "<none>")
            raise RedirectNotAllowed(
                f"refused to follow redirect from {url} -> {location}"
            )
        resp.raise_for_status()
        return resp.json()
