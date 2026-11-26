# ats-scanner

A zero-token, watchlist-based job scanner. It polls a curated list of companies'
public ATS boards (Greenhouse, Lever) for new postings, filters them by title and
location, drops ones already reported, and writes the new matches to disk. No LLM
tokens, no browser, no auth.

It is a **watchlist** tool: it watches companies you already know you care about. It
does not discover unknown companies. It complements broad keyword discovery rather than
replacing it.

This is a Python port of the zero-token scanner in
[career-ops](https://github.com/santifer/career-ops).

## Quickstart

```bash
uv sync
cp config/watchlist.example.yaml config/watchlist.yaml   # edit with your companies
uv run ats-scanner scan --dry-run                        # scan, print, write nothing
uv run ats-scanner scan --prime                          # seed history, report nothing
uv run ats-scanner scan                                  # writes to ./output/
```

## How it works

```
watchlist.yaml  ──►  [ scanner ]  ──►  output/scan-results-DATE.{md,json}   (results)
                          │
                          └──►  data/scan-history.tsv                       (dedup state)
```

1. For each enabled company, a **provider** maps its `careers_url` to the ATS JSON API
   and fetches postings.
2. Postings are filtered by **title** then **location** (case-insensitive substring;
   missing data passes).
3. URLs already in the **scan history** are dropped so you only see what's new.
4. Survivors are written as markdown and JSON. The history TSV is updated.

The results are the deliverable. The history TSV is internal state — it stays with the
tool and is never meant to travel into a vault or notes system.

## CLI

```
ats-scanner scan
  --config PATH     watchlist YAML (default: config/watchlist.yaml)
  --out DIR         output directory (default: ./output)
  --history PATH    dedup TSV (default: ./data/scan-history.tsv)
  --no-md           skip markdown output
  --no-json         skip JSON output
  --dry-run         scan and print counts; write nothing
  --prime           record every current match to history without reporting it
  -v/--verbose      debug logging
```

`--prime` and `--dry-run` are mutually exclusive.

**Prime a newly seeded watchlist before the first real scan.** Adding companies
makes every one of their current postings count as new, so an unprimed first run
reports hundreds of roles at once and is unreadable. Priming records them as seen
and reports nothing; the next scan then shows only what has appeared since.

## Watchlist format

See `config/watchlist.example.yaml`. Companies need a `careers_url` the scanner can map
to an ATS:

- Greenhouse: `https://job-boards.greenhouse.io/<slug>`
- Lever: `https://jobs.lever.co/<slug>`

## Development

```bash
uv run pytest          # tests (offline, mocked HTTP)
uv run ruff check .    # lint
uv run mypy src        # types
```

## Supported ATS providers

| Provider | Careers URL pattern | Ships description |
|----------|--------------------|-------------------|
| Greenhouse | `job-boards.greenhouse.io/<slug>` | no |
| Lever | `jobs.lever.co/<slug>` | yes |

Adding a provider: create `src/ats_scanner/providers/<name>.py` implementing the
`Provider` protocol (`id`, `detect`, `fetch`) with a hostname allowlist, and register it
in `providers/__init__.py`.
