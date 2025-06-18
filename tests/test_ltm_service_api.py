from threading import Thread

import pytest
import requests

from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer
from services.tool_registry import AccessDeniedError, create_default_registry
from tools.ltm_client import consolidate_memory, semantic_consolidate


def _start_server() -> tuple[LTMServiceServer, str]:
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_consolidate_and_retrieve(monkeypatch):
    server, endpoint = _start_server()
    monkeypatch.setenv("LTM_SERVICE_ENDPOINT", endpoint)

    record = {
        "task_context": {"description": "Write docs"},
        "execution_trace": {},
        "outcome": {"success": True},
    }

    resp = requests.post(f"{endpoint}/memory", json={"record": record})
    assert resp.status_code == 201

    resp = requests.get(
        f"{endpoint}/memory", json={"query": {"description": "Write docs"}}
    )
    assert resp.status_code == 200
    assert resp.json()["results"]

    # Test via tool registry
    registry = create_default_registry()

    tool = registry.get_tool("MemoryManager", "retrieve_memory")
    consolidate_memory(record, memory_type="episodic", endpoint=endpoint)
    results = tool(
        {"description": "Write docs"}, memory_type="episodic", endpoint=endpoint
    )
    assert results

    with pytest.raises(AccessDeniedError):
        registry.get_tool("Supervisor", "retrieve_memory")


def test_semantic_consolidate_endpoint():
    server, endpoint = _start_server()
    triple = {"subject": "Transformer", "predicate": "IS_A", "object": "Model"}
    resp = requests.post(
        f"{endpoint}/semantic_consolidate",
        json={"payload": triple},
    )
    assert resp.status_code == 201
    semantic_consolidate(triple, endpoint=endpoint)
    resp = requests.get(
        f"{endpoint}/memory",
        json={"query": triple},
        params={"memory_type": "semantic"},
    )
    assert resp.status_code == 200
    assert resp.json()["results"]
    server.httpd.shutdown()


def test_invalid_memory_type_and_rbac():
    server, endpoint = _start_server()

    # invalid memory type
    resp = requests.post(
        f"{endpoint}/memory",
        json={"record": {}, "memory_type": "invalid"},
        headers={"X-Role": "editor"},
    )
    assert resp.status_code == 400
    assert "memory type" in resp.json()["error"]

    resp = requests.get(
        f"{endpoint}/memory",
        params={"memory_type": "bad"},
        headers={"X-Role": "viewer"},
        json={"query": {}},
    )
    assert resp.status_code == 400

    # unauthorized role
    resp = requests.post(
        f"{endpoint}/memory",
        json={"record": {}},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 403

    resp = requests.get(f"{endpoint}/memory", headers={"X-Role": "guest"})
    assert resp.status_code == 403

    server.httpd.shutdown()


def test_schema_validation_and_forget():
    server, endpoint = _start_server()
    record = {
        "task_context": {"description": "Temp"},
        "execution_trace": {},
        "outcome": {},
    }
    resp = requests.post(f"{endpoint}/memory", json={"record": record})
    assert resp.status_code == 201
    rec_id = resp.json()["id"]

    resp = requests.post(f"{endpoint}/memory", json={}, headers={"X-Role": "editor"})
    assert resp.status_code == 422

    resp = requests.delete(
        f"{endpoint}/forget/{rec_id}",
        headers={"X-Role": "editor"},
        json={"hard": False},
    )
    assert resp.status_code == 200

    resp = requests.get(
        f"{endpoint}/memory",
        json={"query": {"description": "Temp"}},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 200
    assert not resp.json()["results"]

    server.httpd.shutdown()


def test_propagate_subgraph_endpoint():
    server, endpoint = _start_server()
    subgraph = {
        "entities": [{"id": "E1"}, {"id": "E2"}],
        "relations": [{"subject": "E1", "predicate": "LINKS_TO", "object": "E2"}],
    }
    resp = requests.post(f"{endpoint}/propagate_subgraph", json=subgraph)
    assert resp.status_code == 200
    stored = server.service.retrieve(
        "semantic",
        {"subject": "E1", "predicate": "LINKS_TO", "object": "E2"},
    )
    assert stored
    server.httpd.shutdown()


def test_provenance_endpoint():
    server, endpoint = _start_server()
    record = {
        "task_context": {"description": "prov"},
        "execution_trace": {},
        "outcome": {},
        "source": "tester",
    }
    resp = requests.post(f"{endpoint}/memory", json={"record": record})
    assert resp.status_code == 201
    rid = resp.json()["id"]

    resp = requests.get(f"{endpoint}/provenance/episodic/{rid}")
    assert resp.status_code == 200
    assert resp.json()["provenance"]["source"] == "tester"
    server.httpd.shutdown()


def test_rbac_and_memory_type_validation_on_forget_and_provenance():
    server, endpoint = _start_server()

    # unauthorized role for forget
    resp = requests.delete(f"{endpoint}/forget/abc", headers={"X-Role": "viewer"})
    assert resp.status_code == 403

    # invalid memory type for forget
    resp = requests.delete(
        f"{endpoint}/forget/abc",
        headers={"X-Role": "editor"},
        params={"memory_type": "bad"},
        json={"hard": False},
    )
    assert resp.status_code == 400

    # invalid memory type for provenance
    resp = requests.get(f"{endpoint}/provenance/bad/123", headers={"X-Role": "viewer"})
    assert resp.status_code == 400

    server.httpd.shutdown()


def test_skill_endpoint_validation_and_rbac():
    server, endpoint = _start_server()

    resp = requests.post(f"{endpoint}/skill", headers={"X-Role": "viewer"}, json={})
    assert resp.status_code == 403

    resp = requests.post(
        f"{endpoint}/skill",
        headers={"X-Role": "editor"},
        json={"skill_policy": {"steps": []}},
    )
    assert resp.status_code == 400

    server.httpd.shutdown()


def test_skill_query_validation_and_rbac():
    server, endpoint = _start_server()

    resp = requests.post(
        f"{endpoint}/skill_vector_query",
        headers={"X-Role": "guest"},
        json={"query": "demo"},
    )
    assert resp.status_code == 403

    resp = requests.post(
        f"{endpoint}/skill_metadata_query",
        headers={"X-Role": "viewer"},
        json={"query": "demo"},
    )
    assert resp.status_code == 400

    server.httpd.shutdown()


def test_evaluator_memory_rbac_and_validation():
    server, endpoint = _start_server()

    resp = requests.post(
        f"{endpoint}/evaluator_memory", headers={"X-Role": "editor"}, json={}
    )
    assert resp.status_code == 422

    resp = requests.post(
        f"{endpoint}/evaluator_memory",
        headers={"X-Role": "viewer"},
        json={"critique": {}},
    )
    assert resp.status_code == 403

    resp = requests.get(f"{endpoint}/evaluator_memory", headers={"X-Role": "guest"})
    assert resp.status_code == 403

    server.httpd.shutdown()


def test_temporal_and_spatial_validation_and_rbac():
    server, endpoint = _start_server()

    resp = requests.post(
        f"{endpoint}/temporal_consolidate",
        headers={"X-Role": "viewer"},
        json={},
    )
    assert resp.status_code == 403

    resp = requests.post(
        f"{endpoint}/temporal_consolidate",
        headers={"X-Role": "editor"},
        json={"subject": "S"},
    )
    assert resp.status_code == 400

    resp = requests.get(
        f"{endpoint}/spatial_query",
        headers={"X-Role": "guest"},
    )
    assert resp.status_code == 403

    resp = requests.get(
        f"{endpoint}/spatial_query",
        params={"bbox": "1,2,3", "valid_from": "0", "valid_to": "1"},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 400

    server.httpd.shutdown()


def test_forget_evaluator_errors():
    server, endpoint = _start_server()

    resp = requests.delete(
        f"{endpoint}/forget_evaluator/abc", headers={"X-Role": "viewer"}
    )
    assert resp.status_code == 403

    resp = requests.delete(
        f"{endpoint}/forget_evaluator/abc",
        headers={"X-Role": "editor"},
        json={"hard": False},
    )
    assert resp.status_code == 404

    server.httpd.shutdown()
