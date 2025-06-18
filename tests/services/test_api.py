import json

from fastapi.testclient import TestClient

from services.ltm_service.api import LTMService
from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.openapi_app import create_app
from services.ltm_service.semantic_memory import SpatioTemporalMemoryService


class DummyProcedural:
    def __init__(self) -> None:
        self.storage = InMemoryStorage()


def _create_client():
    service = LTMService(
        EpisodicMemoryService(InMemoryStorage()),
        semantic_memory=SpatioTemporalMemoryService(),
        procedural_memory=DummyProcedural(),
    )
    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    return client, service


def _create_client_with_cred(fetcher, threshold=0.5):
    service = LTMService(
        EpisodicMemoryService(InMemoryStorage()),
        semantic_memory=SpatioTemporalMemoryService(),
        procedural_memory=DummyProcedural(),
        credibility_func=fetcher,
        credibility_threshold=threshold,
    )
    app = create_app(service)
    client = TestClient(app, raise_server_exceptions=False)
    return client, service


def test_temporal_consolidate_merges_versions():
    client, service = _create_client()

    data1 = {
        "subject": "S",
        "predicate": "P",
        "object": "O",
        "value": "v1",
        "valid_from": 0,
        "valid_to": 50,
        "location": {"lat": 1},
    }

    resp = client.post(
        "/temporal_consolidate", json=data1, headers={"X-Role": "editor"}
    )
    assert resp.status_code == 200
    fid = resp.json()["id"]

    data2 = {
        "subject": "S",
        "predicate": "P",
        "object": "O",
        "value": "v2",
        "valid_from": 50,
        "valid_to": None,
        "location": {"lat": 2},
    }

    resp = client.post(
        "/temporal_consolidate", json=data2, headers={"X-Role": "editor"}
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == fid

    facts = service.retrieve(
        "semantic",
        {"subject": "S", "predicate": "P", "object": "O"},
        limit=1,
    )
    assert facts and len(facts[0]["history"]) == 2


def test_openapi_contains_temporal_endpoint():
    client, _ = _create_client()
    schema = client.get("/docs/openapi.json").json()
    assert "/temporal_consolidate" in schema["paths"]


def test_spatial_query_endpoint():
    client, _ = _create_client()

    data1 = {
        "subject": "S",
        "predicate": "P",
        "object": "O",
        "value": "v1",
        "valid_from": 0,
        "valid_to": 20,
        "location": {"lat": 1, "lon": 1},
    }
    client.post("/temporal_consolidate", json=data1, headers={"X-Role": "editor"})

    data2 = {
        "subject": "S",
        "predicate": "P",
        "object": "O",
        "value": "v2",
        "valid_from": 30,
        "valid_to": 60,
        "location": {"lat": 1.5, "lon": 1.5},
    }
    client.post("/temporal_consolidate", json=data2, headers={"X-Role": "editor"})

    resp = client.get(
        "/spatial_query",
        params={"bbox": "0,0,2,2", "valid_from": 40, "valid_to": 50},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["value"] == "v2"


def test_skill_endpoints():
    client, _ = _create_client()

    skill = {
        "skill_policy": {"steps": ["a", "b"]},
        "skill_representation": "demo skill",
        "skill_metadata": {"domain": "demo"},
    }
    resp = client.post("/skill", json=skill, headers={"X-Role": "editor"})
    assert resp.status_code == 200 or resp.status_code == 201
    sid = resp.json()["id"]

    resp = client.post(
        "/skill_vector_query",
        json={"query": "demo skill", "limit": 1},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 200
    assert resp.json()["results"][0]["id"] == sid

    resp = client.post(
        "/skill_metadata_query",
        json={"query": {"domain": "demo"}, "limit": 1},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 200
    assert resp.json()["results"][0]["id"] == sid


def test_memory_rejects_low_credibility_source():
    def fetcher(_src: str) -> float:
        return 0.2

    client, service = _create_client_with_cred(fetcher, threshold=0.5)
    record = {
        "task_context": {"description": "demo"},
        "execution_trace": {},
        "outcome": {},
        "source": "untrusted",
    }
    resp = client.post(
        "/memory",
        json={"record": record, "memory_type": "episodic"},
        headers={"X-Role": "editor"},
    )
    assert resp.status_code >= 400
    assert service.verification_log and not service.verification_log[0]["passed"]
    assert "timestamp" in service.verification_log[0]
    assert service.quarantine_log


def test_memory_accepts_high_credibility_source():
    def fetcher(_src: str) -> float:
        return 0.9

    client, service = _create_client_with_cred(fetcher, threshold=0.5)
    record = {
        "task_context": {"description": "demo"},
        "execution_trace": {},
        "outcome": {},
        "source": "trusted",
    }
    resp = client.post(
        "/memory",
        json={"record": record, "memory_type": "episodic"},
        headers={"X-Role": "editor"},
    )
    assert resp.status_code == 200 or resp.status_code == 201
    assert service.verification_log and service.verification_log[0]["passed"]
    assert "timestamp" in service.verification_log[0]


def test_retrieval_filters_trigger_phrases():
    client, service = _create_client()

    record = {
        "task_context": {"description": "contains AGENTPOISON"},
        "execution_trace": {},
        "outcome": {},
    }
    service.consolidate("episodic", record)

    results = service.retrieve("episodic", {"description": "AGENTPOISON"}, limit=1)
    assert results
    payload = json.dumps(results[0])
    assert "AGENTPOISON" not in payload
    assert service.quarantine_log


def test_skill_queries_filter_trigger_phrases():
    client, service = _create_client()

    sid = service.add_skill(
        {"steps": ["a"]},
        "use skill TRIGGER PHRASE",
        {"domain": "demo"},
    )

    results = service.skill_vector_query("use skill", limit=1)
    assert results
    assert results[0]["id"] == sid
    assert "TRIGGER PHRASE" not in json.dumps(results[0])
    assert service.quarantine_log
