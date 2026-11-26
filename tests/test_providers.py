import pytest

from ats_scanner.http import HttpClient, RedirectNotAllowed
from ats_scanner.models import WatchlistEntry
from ats_scanner.providers import route
from ats_scanner.providers.base import assert_allowed_host
from ats_scanner.providers.greenhouse import GreenhouseProvider
from ats_scanner.providers.lever import LeverProvider

GH_API = "https://boards-api.greenhouse.io/v1/boards/careaccess/jobs"
LEVER_API = "https://api.lever.co/v0/postings/example"


def test_greenhouse_detect_from_careers_url():
    entry = WatchlistEntry(name="Care Access", careers_url="https://job-boards.greenhouse.io/careaccess")
    assert GreenhouseProvider().detect(entry) == GH_API


def test_greenhouse_detect_from_explicit_api():
    entry = WatchlistEntry(name="X", api=GH_API)
    assert GreenhouseProvider().detect(entry) == GH_API


def test_greenhouse_fetch_parses_jobs(httpx_mock, greenhouse_payload):
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    entry = WatchlistEntry(name="Care Access", careers_url="https://job-boards.greenhouse.io/careaccess")
    with HttpClient() as http:
        jobs = GreenhouseProvider().fetch(entry, http)
    # 5 jobs in fixture, all with absolute_url -> 5 parsed
    assert len(jobs) == 5
    first = jobs[0]
    assert first.title == "Senior Data Engineer"
    assert first.url == "https://job-boards.greenhouse.io/careaccess/jobs/4112890009"
    assert first.company == "Care Access"
    assert first.location == "Remote - US"
    assert first.posted_at is not None
    # empty location / null date tolerated
    staff = [j for j in jobs if j.title == "Staff Data Engineer"][0]
    assert staff.location == ""
    assert staff.posted_at is None


def test_lever_detect_and_fetch(httpx_mock, lever_payload):
    httpx_mock.add_response(url=LEVER_API, json=lever_payload)
    entry = WatchlistEntry(name="Example", careers_url="https://jobs.lever.co/example")
    assert LeverProvider().detect(entry) == LEVER_API
    with HttpClient() as http:
        jobs = LeverProvider().fetch(entry, http)
    assert len(jobs) == 2
    assert jobs[0].title == "Data Platform Engineer"
    assert jobs[0].url == "https://jobs.lever.co/example/abc-123"
    # Lever ships description for free
    assert "data platform" in jobs[0].description.lower()
    assert jobs[0].posted_at is not None


def test_route_picks_correct_provider():
    gh = WatchlistEntry(name="A", careers_url="https://job-boards.greenhouse.io/a")
    lv = WatchlistEntry(name="B", careers_url="https://jobs.lever.co/b")
    none = WatchlistEntry(name="C", careers_url="https://example.com/careers")
    assert route(gh).id == "greenhouse"
    assert route(lv).id == "lever"
    assert route(none) is None


def test_route_honors_explicit_provider_override():
    entry = WatchlistEntry(name="A", careers_url="https://jobs.lever.co/a", provider="lever")
    assert route(entry).id == "lever"


def test_http_refuses_to_follow_redirect(httpx_mock):
    httpx_mock.add_response(
        url=GH_API, status_code=302, headers={"location": "http://169.254.169.254/"}
    )
    with HttpClient() as http:
        with pytest.raises(RedirectNotAllowed):
            http.get_json(GH_API)


def test_assert_allowed_host_rejects_off_allowlist():
    with pytest.raises(ValueError):
        assert_allowed_host("https://evil.example.com/jobs", {"boards-api.greenhouse.io"})


def test_assert_allowed_host_rejects_non_https():
    with pytest.raises(ValueError):
        assert_allowed_host("http://boards-api.greenhouse.io/x", {"boards-api.greenhouse.io"})
