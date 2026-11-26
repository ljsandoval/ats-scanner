"""Load and validate the watchlist YAML into a Watchlist model.

Mirrors the yaml + pydantic pattern used in telegram-brainbot's src/config.py.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Watchlist


def load_watchlist(path: str | Path) -> Watchlist:
    """Read watchlist.yaml and validate it. Raises FileNotFoundError if missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"watchlist config not found: {p} "
            "(copy config/watchlist.example.yaml to config/watchlist.yaml)"
        )
    with open(p) as f:
        raw = yaml.safe_load(f) or {}
    return Watchlist.model_validate(raw)
