"""Render scan results as markdown and/or JSON.

The results are the deliverable ("new matching roles this run") — a fresh snapshot per
run, not appended. The markdown mirrors the /job-scout summary table so the two feel
consistent. Files are written to a configurable output directory.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Job


def render_markdown(jobs: list[Job], run_dt: datetime) -> str:
    header = f"# Scan Results — {run_dt:%Y-%m-%d %H:%M}\n\n"
    if not jobs:
        return header + "_No new matching roles this run._\n"
    lines = [
        header,
        f"**{len(jobs)} new role(s).**\n",
        "| Company | Role | Location | Posted | URL |",
        "|---------|------|----------|--------|-----|",
    ]
    for j in sorted(jobs, key=lambda x: (x.company.lower(), x.title.lower())):
        posted = f"{j.posted_at:%Y-%m-%d}" if j.posted_at else "—"
        location = j.location or "—"
        lines.append(
            f"| {j.company} | {j.title} | {location} | {posted} | {j.url} |"
        )
    return "\n".join(lines) + "\n"


def render_json(jobs: list[Job], run_dt: datetime) -> str:
    payload = {
        "generated_at": run_dt.isoformat(),
        "count": len(jobs),
        "jobs": [j.model_dump(mode="json") for j in jobs],
    }
    return json.dumps(payload, indent=2)


def write_outputs(
    jobs: list[Job],
    out_dir: str | Path,
    *,
    run_dt: datetime | None = None,
    md: bool = True,
    json_: bool = True,
) -> list[Path]:
    """Write enabled formats to out_dir. Returns the paths written."""
    run_dt = run_dt or datetime.now()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = run_dt.strftime("%Y-%m-%d")
    written: list[Path] = []
    if md:
        p = out / f"scan-results-{stamp}.md"
        p.write_text(render_markdown(jobs, run_dt))
        written.append(p)
    if json_:
        p = out / f"scan-results-{stamp}.json"
        p.write_text(render_json(jobs, run_dt))
        written.append(p)
    return written
