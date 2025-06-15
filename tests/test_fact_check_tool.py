import importlib
from typing import Any

import pytest

fc = importlib.import_module("tools.fact_check")


class DummyResponse:
    def __init__(self, data: Any) -> None:
        self._data = data
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return self._data


def test_fact_check_parses_response(monkeypatch):
    data = {
        "claims": [
            {
                "text": "Earth is flat",
                "claimReview": [
                    {
                        "url": "http://example.com",
                        "reviewRating": {"text": "False"},
                    }
                ],
            }
        ]
    }

    def fake_get(url: str, params: Any, timeout: int) -> DummyResponse:
        assert params["query"] == "Earth is flat"
        return DummyResponse(data)

    monkeypatch.setenv("FACT_CHECK_API_KEY", "x")
    monkeypatch.setattr(fc.requests, "get", fake_get)
    result = fc.fact_check_claim("Earth is flat")
    assert result["rating"] == "False"
    assert "http://example.com" in result["source_links"]


def test_fact_check_retries_and_errors(monkeypatch):
    calls = []

    def fake_get(url: str, params: Any, timeout: int) -> DummyResponse:
        calls.append(1)
        raise fc.requests.RequestException("boom")

    monkeypatch.setenv("FACT_CHECK_API_KEY", "x")
    monkeypatch.setattr(fc.requests, "get", fake_get)
    monkeypatch.setattr(fc.time, "sleep", lambda s: None)
    with pytest.raises(ValueError):
        fc.fact_check_claim("test", retries=2)
    assert len(calls) == 3
