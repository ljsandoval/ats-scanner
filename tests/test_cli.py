import yaml

from ats_scanner.cli import main

GH_API = "https://boards-api.greenhouse.io/v1/boards/careaccess/jobs"


def _write_config(tmp_path) -> str:
    cfg = {
        "title_filter": {"positive": ["data engineer"], "negative": ["intern"]},
        "location_filter": {"allow": ["Remote", "United States"], "block": ["India"]},
        "tracked_companies": [
            {"name": "Care Access", "careers_url": "https://job-boards.greenhouse.io/careaccess"}
        ],
    }
    path = tmp_path / "watchlist.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return str(path)


def _args(tmp_path, *extra: str) -> list[str]:
    return [
        "scan",
        "--config", _write_config(tmp_path),
        "--out", str(tmp_path / "out"),
        "--history", str(tmp_path / "h.tsv"),
        *extra,
    ]


def test_prime_records_history_and_writes_no_output(
    httpx_mock, tmp_path, greenhouse_payload, capsys
):
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    assert main(_args(tmp_path, "--prime")) == 0

    out = capsys.readouterr().out
    assert "[prime]" in out
    assert "nothing reported" in out
    # History seeded, no output directory created.
    assert (tmp_path / "h.tsv").exists()
    assert not (tmp_path / "out").exists()


def test_scan_after_prime_reports_nothing_new(httpx_mock, tmp_path, greenhouse_payload, capsys):
    """The whole point of priming: the first real scan is not flooded."""
    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    main(_args(tmp_path, "--prime"))

    httpx_mock.add_response(url=GH_API, json=greenhouse_payload)
    assert main(_args(tmp_path)) == 0
    assert "0 new /" in capsys.readouterr().out


def test_prime_and_dry_run_are_mutually_exclusive(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        main(_args(tmp_path, "--prime", "--dry-run"))
