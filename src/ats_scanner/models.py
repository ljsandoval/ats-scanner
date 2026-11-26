"""Data models — the normalized job and the watchlist config schema.

These are the Python equivalent of career-ops's `providers/_types.js` JSDoc typedefs,
except pydantic validates them at runtime instead of being doc-only hints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Job(BaseModel):
    """A normalized job posting — the unit of currency throughout the scanner.

    `url` is the dedup key. `description` is populated only when a provider's list
    payload carries it for free (Lever does; Greenhouse does not) — the scanner never
    makes a second per-job request.
    """

    title: str
    url: str
    company: str
    location: str = ""
    description: str = ""
    posted_at: datetime | None = None


class WatchlistEntry(BaseModel):
    """One tracked company from the watchlist."""

    name: str
    careers_url: str = ""
    enabled: bool = True
    # Optional overrides:
    provider: str | None = None  # force a provider id, bypassing detect()
    api: str | None = None  # explicit API URL (Greenhouse only)


class TitleFilter(BaseModel):
    positive: list[str] = Field(default_factory=list)
    negative: list[str] = Field(default_factory=list)


class LocationFilter(BaseModel):
    always_allow: list[str] = Field(default_factory=list)
    allow: list[str] = Field(default_factory=list)
    block: list[str] = Field(default_factory=list)


class ScanHistoryConfig(BaseModel):
    recheck_after_days: int | None = None


class Watchlist(BaseModel):
    """The full watchlist.yaml, validated."""

    title_filter: TitleFilter = Field(default_factory=TitleFilter)
    location_filter: LocationFilter = Field(default_factory=LocationFilter)
    scan_history: ScanHistoryConfig = Field(default_factory=ScanHistoryConfig)
    tracked_companies: list[WatchlistEntry] = Field(default_factory=list)
