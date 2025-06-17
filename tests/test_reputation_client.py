import importlib
from typing import Any

import pytest

rc = importlib.import_module("tools.reputation_client")


class DummyResp:
    def __init__(self, data: Any) -> None:
        self._data = data
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return self._data


def test_publish_reputation_event(monkeypatch):
    def fake_post(url: str, json: Any, headers: Any, timeout: int) -> DummyResp:
        assert json["agent_id"] == "A"
        assert "Authorization" in headers
        return DummyResp({"evaluation_id": "1"})

    monkeypatch.setattr(rc.requests, "post", fake_post)
    result = rc.publish_reputation_event({"agent_id": "A"})
    assert result == "1"


def test_publish_reputation_event_retries(monkeypatch):
    calls = []

    def fake_post(url: str, json: Any, headers: Any, timeout: int) -> DummyResp:
        calls.append(1)
        raise rc.requests.RequestException("fail")

    monkeypatch.setattr(rc.requests, "post", fake_post)
    monkeypatch.setattr(rc.time, "sleep", lambda s: None)
    with pytest.raises(ValueError):
        rc.publish_reputation_event({"agent_id": "A"}, retries=2)
    assert len(calls) == 3
