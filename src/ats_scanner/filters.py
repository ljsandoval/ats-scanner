"""Title and location filters — case-insensitive substring matching.

Ported from career-ops's buildTitleFilter / buildLocationFilter in scan.mjs. The
guiding rule everywhere: missing data passes (never reject a posting for an empty
field).
"""

from __future__ import annotations

from .models import Job, LocationFilter, TitleFilter


def _matches_any(haystack: str, needles: list[str]) -> bool:
    lower = haystack.lower()
    return any(n.lower() in lower for n in needles)


def title_passes(title: str, f: TitleFilter) -> bool:
    if f.negative and _matches_any(title, f.negative):
        return False
    if not f.positive:
        return True
    return _matches_any(title, f.positive)


def location_passes(location: str, f: LocationFilter) -> bool:
    # Order matters and mirrors career-ops exactly.
    if not location.strip():
        return True  # empty location -> pass (don't penalize missing data)
    if f.always_allow and _matches_any(location, f.always_allow):
        return True  # rescues multi-location postings naming your home region
    if f.block and _matches_any(location, f.block):
        return False
    if not f.allow:
        return True  # no allow list -> already cleared block, pass
    return _matches_any(location, f.allow)


def apply_title_filter(jobs: list[Job], f: TitleFilter) -> list[Job]:
    return [j for j in jobs if title_passes(j.title, f)]


def apply_location_filter(jobs: list[Job], f: LocationFilter) -> list[Job]:
    return [j for j in jobs if location_passes(j.location, f)]
