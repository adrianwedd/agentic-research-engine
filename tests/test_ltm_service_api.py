from threading import Thread

import pytest
import requests

from services.ltm_service.api import LTMService, LTMServiceServer
from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage
from services.tool_registry import AccessDeniedError, ToolRegistry
from tools.ltm_client import consolidate_memory, retrieve_memory


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
    registry = ToolRegistry()
    registry.register_tool(
        "consolidate_memory", consolidate_memory, allowed_roles=["MemoryManager"]
    )
    registry.register_tool(
        "retrieve_memory", retrieve_memory, allowed_roles=["MemoryManager"]
    )

    tool = registry.get_tool("MemoryManager", "retrieve_memory")
    consolidate_memory(record, memory_type="episodic", endpoint=endpoint)
    results = tool(
        {"description": "Write docs"}, memory_type="episodic", endpoint=endpoint
    )
    assert results

    with pytest.raises(AccessDeniedError):
        registry.get_tool("Supervisor", "retrieve_memory")
