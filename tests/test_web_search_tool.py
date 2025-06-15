import importlib
from typing import Any

ws = importlib.import_module("tools.web_search")


class DummyResponse:
    def __init__(self, data: Any) -> None:
        self._data = data
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return self._data


def test_web_search_parses_results(monkeypatch):
    def fake_post(url: str, json: Any, headers: Any, timeout: int) -> DummyResponse:
        assert json["q"] == "multi-agent systems"
        return DummyResponse(
            {
                "organic": [
                    {"link": "http://example.com", "title": "Example", "snippet": "A"}
                ]
            }
        )

    monkeypatch.setenv("SEARCH_API_KEY", "x")
    monkeypatch.setattr(ws.requests, "post", fake_post)
    results = ws.web_search("multi-agent systems")
    assert results == [
        {"url": "http://example.com", "title": "Example", "snippet": "A"}
    ]
