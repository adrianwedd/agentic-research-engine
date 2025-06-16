import json
from pathlib import Path
from unittest import mock

import pytest

from scripts import score_metrics, scrape_repos

pytestmark = pytest.mark.core


def test_search_repos_pagination():
    resp1 = mock.Mock()
    resp1.status_code = 200
    resp1.json.return_value = {"items": [{"id": 1}]}
    resp1.links = {"next": {"url": "n"}}
    resp2 = mock.Mock()
    resp2.status_code = 200
    resp2.json.return_value = {"items": [{"id": 2}]}
    resp2.links = {}
    with mock.patch.object(
        scrape_repos.requests, "get", side_effect=[resp1, resp2]
    ) as m:
        results = scrape_repos.search_repos(50)
    assert len(results) == 2
    assert m.call_count == 2


def test_main_writes_output(tmp_path: Path):
    out = tmp_path / "repos.json"
    with mock.patch.object(scrape_repos, "fetch_repo", return_value={"id": 1}):
        scrape_repos.main(["--repos", "u/r", "--output", str(out)])
    data = json.loads(out.read_text())
    assert data == [{"id": 1}]


def test_compute_metrics():
    repos = [
        {"stargazers_count": 5, "forks_count": 1},
        {"stargazers_count": 3, "forks_count": 3},
    ]
    metrics = score_metrics.compute_metrics(repos)
    assert metrics == {"repo_count": 2, "avg_stars": 4.0, "avg_forks": 2.0}
