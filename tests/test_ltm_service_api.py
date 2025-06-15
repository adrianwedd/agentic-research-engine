from threading import Thread

import pytest
import requests

from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer
from services.tool_registry import AccessDeniedError, create_default_registry
from tools.ltm_client import consolidate_memory


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

    resp = requests.post(f"{endpoint}/consolidate", json={"record": record})
    assert resp.status_code == 201

    resp = requests.get(
        f"{endpoint}/retrieve", json={"query": {"description": "Write docs"}}
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


def test_invalid_memory_type_and_rbac():
    server, endpoint = _start_server()

    # invalid memory type
    resp = requests.post(
        f"{endpoint}/consolidate",
        json={"record": {}, "memory_type": "invalid"},
        headers={"X-Role": "editor"},
    )
    assert resp.status_code == 400
    assert "memory type" in resp.json()["error"]

    resp = requests.get(
        f"{endpoint}/retrieve",
        params={"memory_type": "bad"},
        headers={"X-Role": "viewer"},
        json={"query": {}},
    )
    assert resp.status_code == 400

    # unauthorized role
    resp = requests.post(
        f"{endpoint}/consolidate",
        json={"record": {}},
        headers={"X-Role": "viewer"},
    )
    assert resp.status_code == 403

    resp = requests.get(f"{endpoint}/retrieve", headers={"X-Role": "guest"})
    assert resp.status_code == 403

    server.httpd.shutdown()
