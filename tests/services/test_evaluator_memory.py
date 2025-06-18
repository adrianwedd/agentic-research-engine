import json

from fastapi.testclient import TestClient

from services.ltm_service.api import LTMService
from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.openapi_app import create_app


class DummyProcedural:
    def __init__(self) -> None:
        self.storage = InMemoryStorage()


def _create_client():
    service = LTMService(
        EpisodicMemoryService(InMemoryStorage()),
        procedural_memory=DummyProcedural(),
    )
    app = create_app(service)
    client = TestClient(app)
    return client, service


def test_store_and_retrieve_critique():
    client, service = _create_client()
    critique = {
        "prompt": "Q?",
        "outcome": "fail",
        "risk_categories": ["bias"],
        "overall_score": 0.4,
        "criteria_breakdown": {"accuracy": 0.3},
        "feedback_text": "bad",
        "created_at": 1.0,
        "updated_at": 1.0,
    }
    resp = client.post(
        "/evaluator_memory", json={"critique": critique}, headers={"X-Role": "editor"}
    )
    assert resp.status_code == 200 or resp.status_code == 201
    cid = resp.json()["id"]

    resp = client.request(
        "GET",
        "/evaluator_memory",
        json={"query": {"prompt": "Q?"}},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    assert any(
        r.get("prompt") == "Q?" or r.get("task_context", {}).get("prompt") == "Q?"
        for r in results
    )

    direct = service.retrieve_evaluator_memory({"prompt": "Q?"}, limit=1)
    assert direct
    assert cid == direct[0].get("id")


def test_evaluator_memory_filters_trigger_phrases():
    client, service = _create_client()

    critique = {
        "prompt": "bad TRIGGER PHRASE",  # suspicious content
        "outcome": "fail",
    }
    resp = client.post(
        "/evaluator_memory",
        json={"critique": critique},
        headers={"X-Role": "editor"},
    )
    assert resp.status_code == 200 or resp.status_code == 201

    results = service.retrieve_evaluator_memory({"prompt": "bad"}, limit=1)
    assert results
    assert "TRIGGER PHRASE" not in json.dumps(results[0])
    assert service.quarantine_log

    resp = client.request(
        "GET",
        "/evaluator_memory",
        json={"query": {"prompt": "bad"}},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 200
    payload = json.dumps(resp.json()["results"][0])
    assert "TRIGGER PHRASE" not in payload
