# CLAUDE.md — ats-scanner

Zero-token watchlist job scanner. Polls public ATS APIs (Greenhouse, Lever) for new
postings, filters by title/location, dedups, writes markdown + JSON. Python port of the
scanner in `~/code/external/career-ops/`.

## Conventions

- Python 3.11, `uv` + `hatchling`, `src/` layout (`src/ats_scanner/`).
- Deps: `httpx`, `pydantic`, `pyyaml`. Dev: `pytest`, `pytest-httpx`, `ruff`, `mypy`.
- Run: `uv run ats-scanner scan` or `uv run python -m ats_scanner scan`.
- Test: `uv run pytest`. Lint: `uv run ruff check .`. Types: `uv run mypy src`.

## Architecture

- `models.py` — pydantic: `Job` (dedup key = `url`), `WatchlistEntry`, filters, `Watchlist`.
- `http.py` — `HttpClient`; **`follow_redirects=False`** is a deliberate SSRF guard, do
  not remove. Providers validate hostnames against an allowlist; a followed redirect
  would bypass that.
- `providers/` — one module per ATS. `Provider` protocol: `id`, `detect(entry)`,
  `fetch(entry, http)`. Each has a hostname allowlist enforced via `assert_allowed_host`.
- `filters.py` — case-insensitive substring; missing data passes.
- `history.py` — TSV dedup ledger. Internal STATE, never an output; stays with the tool.
- `scanner.py` — orchestrator; one failing board is logged and skipped, never aborts.
- `output.py` — markdown + JSON, fresh snapshot per run.
- `cli.py` — argparse `scan` subcommand.

## Design rules

- Zero tokens, no browser, no per-job requests. Only fetch a company's list endpoint.
- Watchlist model only (known companies). Discovery of unknown companies is out of scope.
- Faithful to career-ops filter/dedup semantics — see that repo's `scan.mjs` and
  `providers/*.mjs` when extending.

## Roadmap

Phase 2: salary filter, Ashby + Workday providers, watchlist seeding.
Phase 3: vault/Syncthing output wiring, Dockerfile, Pi scheduling.
Later: keyword-based discovery (possibly a sibling tool).
