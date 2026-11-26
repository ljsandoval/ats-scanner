from datetime import date, timedelta

from ats_scanner.history import ScanHistory
from ats_scanner.models import Job


def _job(url: str) -> Job:
    return Job(title="Data Engineer", url=url, company="X")


def test_record_and_dedup(tmp_path):
    path = tmp_path / "history.tsv"
    h = ScanHistory(path)
    added = h.record([_job("https://a/1"), _job("https://a/2")])
    assert added == 2

    # A fresh instance reads the file back and dedups.
    h2 = ScanHistory(path)
    assert h2.is_seen("https://a/1") is True
    assert h2.is_seen("https://a/3") is False


def test_record_is_idempotent(tmp_path):
    path = tmp_path / "history.tsv"
    h = ScanHistory(path)
    assert h.record([_job("https://a/1")]) == 1
    assert h.record([_job("https://a/1")]) == 0  # already seen, not re-added


def test_recheck_after_days_reeligibility(tmp_path):
    path = tmp_path / "history.tsv"
    # Seed a row seen 40 days ago.
    old = (date.today() - timedelta(days=40)).isoformat()
    path.write_text(f"url\tstatus\tfirst_seen\nhttps://a/1\tactive\t{old}\n")

    fresh = ScanHistory(path, recheck_after_days=30)
    # 40 days > 30 day window -> eligible again (not "seen")
    assert fresh.is_seen("https://a/1") is False

    forever = ScanHistory(path)  # no recheck window -> deduped forever
    assert forever.is_seen("https://a/1") is True


def test_header_row_not_treated_as_url(tmp_path):
    path = tmp_path / "history.tsv"
    h = ScanHistory(path)
    h.record([_job("https://a/1")])
    h2 = ScanHistory(path)
    assert h2.is_seen("url") is False
