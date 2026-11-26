import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    with open(FIXTURES / name) as f:
        return json.load(f)


@pytest.fixture
def greenhouse_payload():
    return _load("greenhouse_jobs.json")


@pytest.fixture
def lever_payload():
    return _load("lever_postings.json")
