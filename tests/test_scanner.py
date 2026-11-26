from ats_scanner.history import ScanHistory
from ats_scanner.http import HttpClient
from ats_scanner.models import (
    LocationFilter,
    TitleFilter,
    Watchlist,
    WatchlistEntry,
)
from ats_scanner.scanner import run_scan

GH_API = "https://boards-api.greenhouse.io/v1/boards/careaccess/jobs"
LEVER_API = "https://api.lever.co/v0/postings/example"


def _watchlist() -> Watchlist:
    return Watchlist(
        title_filter=TitleFilter(positive=["data engineer", "data platform"], negative=["intern"]),
        location_filter=LocationFilter(
            always_allow=["Portland"], allow=["Remote", "United States"], block=["India"]
        ),
        tracked_companies=[
            WatchlistEntry(name="Care Access", careers_url="https://job-boards.greenhouse.io/careaccess"),
            WatchlistEntry(name="Example", careers_url="https://jobs.lever.co/example"),
        ],
    )


def test_full_scan_filters_and_dedups(httpx_mock, tmp_path, greenhouse_payload, lever_payload):
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)

    history = ScanHistory(tmp_path / "h.tsv")
    with HttpClient() as http:
        result = run_scan(_watchlist(), http, history)

    titles = {j.title for j in result.new_jobs}
    # Greenhouse: Senior DE (remote), Staff DE (empty loc) pass.
    #   Marketing Manager (no positive), DE in India (blocked), Intern (negative) drop.
    # Lever: Data Platform Engineer (remote) passes; Account Executive (no positive) drops.
    assert titles == {"Senior Data Engineer", "Staff Data Engineer", "Data Platform Engineer"}
    assert result.companies_scanned == 2
    assert result.total_fetched == 7  # 5 greenhouse + 2 lever, before filtering
    assert result.errors == []


def test_seen_jobs_are_not_re_reported(httpx_mock, tmp_path, greenhouse_payload, lever_payload):
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)

    history = ScanHistory(tmp_path / "h.tsv")
    with HttpClient() as http:
        first = run_scan(_watchlist(), http, history)
    history.record(first.new_jobs)

    # Second run, same payloads -> nothing new.
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)
    with HttpClient() as http:
        second = run_scan(_watchlist(), http, history)
    assert second.new_jobs == []


def test_unmatched_company_records_error_but_continues(httpx_mock, tmp_path, lever_payload):
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)
    wl = Watchlist(
        title_filter=TitleFilter(positive=["data platform"]),
        tracked_companies=[
            WatchlistEntry(name="Unknown", careers_url="https://example.com/careers"),
            WatchlistEntry(name="Example", careers_url="https://jobs.lever.co/example"),
        ],
    )
    history = ScanHistory(tmp_path / "h.tsv")
    with HttpClient() as http:
        result = run_scan(wl, http, history)
    assert len(result.errors) == 1
    assert result.errors[0][0] == "Unknown"
    assert {j.title for j in result.new_jobs} == {"Data Platform Engineer"}


def test_matched_jobs_holds_everything_new_jobs_filters(
    httpx_mock, tmp_path, greenhouse_payload, lever_payload
):
    """matched_jobs ignores history; new_jobs is the subset not seen before."""
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)

    history = ScanHistory(tmp_path / "h.tsv")
    with HttpClient() as http:
        first = run_scan(_watchlist(), http, history)
    history.record(first.new_jobs)

    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)
    with HttpClient() as http:
        second = run_scan(_watchlist(), http, history)

    assert second.new_jobs == []  # all already reported
    assert len(second.matched_jobs) == 3  # but still matching the filters
