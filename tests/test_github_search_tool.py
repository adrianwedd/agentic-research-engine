import importlib
import time
from typing import Any

import pytest

gs = importlib.import_module("tools.github_search")


class DummyResponse:
    def __init__(
        self, status_code: int, data: Any, headers: dict | None = None
    ) -> None:
        self.status_code = status_code
        self._data = data
        self.headers = headers or {}
        self.text = str(data)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise gs.requests.HTTPError(f"{self.status_code}", response=self)

    def json(self) -> Any:
        return self._data


def test_repo_search_parses_results(monkeypatch):
    data = {
        "items": [
            {
                "html_url": "http://github.com/example/repo",
                "full_name": "example/repo",
                "description": "Test repo",
            }
        ]
    }

    def fake_get(url: str, headers: Any, params: Any, timeout: int) -> DummyResponse:
        assert params["q"] == "langchain"
        return DummyResponse(200, data)

    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(gs.requests, "get", fake_get)
    results = gs.github_search("langchain")
    assert results == [
        {
            "url": "http://github.com/example/repo",
            "name": "example/repo",
            "description": "Test repo",
        }
    ]


def test_repo_search_rate_limit(monkeypatch):
    calls = []

    def fake_get(url: str, headers: Any, params: Any, timeout: int) -> DummyResponse:
        calls.append(1)
        headers_resp = {"X-RateLimit-Reset": str(int(time.time()) + 1)}
        return DummyResponse(403, {"message": "rate limit exceeded"}, headers_resp)

    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setattr(gs.requests, "get", fake_get)
    monkeypatch.setattr(gs.time, "sleep", lambda s: None)
    with pytest.raises(ValueError):
        gs.github_search("query", retries=1)
    assert len(calls) == 2


def test_empty_query(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    with pytest.raises(ValueError):
        gs.github_search("  ")
