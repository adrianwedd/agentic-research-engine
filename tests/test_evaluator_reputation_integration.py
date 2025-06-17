import importlib
from typing import Any

from agents.evaluator import EvaluatorAgent

rc = importlib.import_module("tools.reputation_client")


class DummyResp:
    def __init__(self) -> None:
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return {"evaluation_id": "1"}


def test_evaluator_publishes_reputation(monkeypatch):
    calls = {}

    def fake_post(url: str, json: Any, headers: Any, timeout: int) -> DummyResp:
        calls.update(json)
        return DummyResp()

    monkeypatch.setattr(rc.requests, "post", fake_post)
    agent = EvaluatorAgent()
    agent.evaluate_and_publish(
        {"text": "a"},
        {},
        task_id="w1",
        worker_agent_id="A1",
        evaluator_id="E1",
        is_final=True,
    )
    assert calls.get("agent_id") == "A1"
    assert calls.get("workflow_id") == "w1"
