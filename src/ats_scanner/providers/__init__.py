"""Provider registry and routing.

`route(entry)` picks the provider for a company: an explicit `provider:` id wins,
otherwise the first provider whose `detect()` claims the entry (career-ops's
detect-based routing).
"""

from __future__ import annotations

from ..models import WatchlistEntry
from .base import Provider
from .greenhouse import GreenhouseProvider
from .lever import LeverProvider

REGISTRY: list[Provider] = [GreenhouseProvider(), LeverProvider()]

_BY_ID = {p.id: p for p in REGISTRY}


def route(entry: WatchlistEntry) -> Provider | None:
    """Return the provider that should handle this entry, or None."""
    if entry.provider:
        return _BY_ID.get(entry.provider)
    for provider in REGISTRY:
        if provider.detect(entry) is not None:
            return provider
    return None
