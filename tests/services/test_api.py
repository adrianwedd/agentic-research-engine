from fastapi.testclient import TestClient

from services.ltm_service.api import LTMService
from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.openapi_app import create_app
from services.ltm_service.semantic_memory import SpatioTemporalMemoryService


def _create_client():
    service = LTMService(
        EpisodicMemoryService(InMemoryStorage()),
        semantic_memory=SpatioTemporalMemoryService(),
    )
    app = create_app(service)
    client = TestClient(app)
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
