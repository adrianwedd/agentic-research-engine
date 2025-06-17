from threading import Thread

import requests

from agents.code_researcher import CodeResearcherAgent
from agents.web_researcher import WebResearcherAgent
from engine.orchestration_engine import GraphState
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer
from services.tool_registry import create_default_registry


def _start_server():
    episodic = EpisodicMemoryService(InMemoryStorage())
    service = LTMService(episodic)
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_matching_procedure_executed():
    server, endpoint = _start_server()
    record = {
        "task_context": {"sub_task": "Add numbers"},
        "procedure": [{"action": "add", "args": [2, 2]}],
        "outcome": {"success": True},
    }
    requests.post(
        f"{endpoint}/memory",
        headers={"X-Role": "editor"},
        json={"record": record, "memory_type": "procedural"},
    )
    registry = create_default_registry()
    agent = WebResearcherAgent(registry, ltm_endpoint=endpoint)
    state = GraphState(data={"sub_task": "Add numbers"})
    result = agent(state, {})
    assert result.data.get("procedure_result") == [4]
    server.httpd.shutdown()


def test_fallback_when_no_match():
    server, endpoint = _start_server()
    registry = create_default_registry()
    agent = CodeResearcherAgent(registry, ltm_endpoint=endpoint)
    code = "result = 1 + 1\nprint(result)"
    state = GraphState(data={"code": code, "code_args": []})
    result = agent(state, {})
    assert "code_result" in result.data
    server.httpd.shutdown()
