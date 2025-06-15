from pathlib import Path
from threading import Thread

import pytest
import requests

from agents.supervisor import State, SupervisorAgent
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer


class DummyGraphState:
    def __init__(self, data=None):
        self.data = data or {}

    def update(self, other):
        self.data.update(other)


def _start_server():
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_analyze_query_returns_state():
    agent = SupervisorAgent()
    state = agent.analyze_query("What is AI?")
    assert isinstance(state, State)
    assert state.initial_query == "What is AI?"


def test_supervisor_node_updates_graph_state():
    agent = SupervisorAgent()
    gs = DummyGraphState({"query": "Example query"})
    result = agent(gs)
    assert isinstance(result.data.get("state"), State)
    assert result.data["state"].initial_query == "Example query"


def test_plan_contains_parallel_webresearcher_nodes():
    agent = SupervisorAgent()
    plan = agent.plan_research_task(
        "Compare the performance of Transformer and LSTM models"
    )
    nodes = plan["graph"]["nodes"]
    topics = [n.get("topic") for n in nodes if n["agent"] == "WebResearcher"]
    assert "Transformer performance" in topics
    assert "LSTM performance" in topics


def test_invalid_query_raises_value_error():
    agent = SupervisorAgent()
    gs = DummyGraphState({"query": None})
    with pytest.raises(ValueError):
        agent(gs)


def test_supervisor_trims_query():
    agent = SupervisorAgent()
    gs = DummyGraphState({"query": "  spaced query \n"})
    result = agent(gs)
    assert result.data["state"].initial_query == "spaced query"


def test_plan_yaml_roundtrip():
    agent = SupervisorAgent()
    plan = agent.plan_research_task(
        "Compare Transformer and LSTM for NLP tasks with accuracy metrics"
    )
    yaml_text = agent.format_plan_as_yaml(plan)
    parsed = agent.parse_plan(yaml_text)
    assert parsed == plan


def test_parse_plan_invalid_yaml_raises():
    agent = SupervisorAgent()
    with pytest.raises(ValueError):
        agent.parse_plan("not: [valid")


def test_parse_plan_schema_violation_raises():
    agent = SupervisorAgent()
    bad_yaml = """
    query: q
    context: []
    graph:
      nodes:
        - id: n1
          agent: WebResearcher
    evaluation:
      metric: quality
    """
    with pytest.raises(ValueError):
        agent.parse_plan(bad_yaml)


def test_plan_research_task_produces_valid_plan():
    agent = SupervisorAgent()
    plan = agent.plan_research_task("What is AI?")
    # should not raise
    agent.validate_plan(plan)


def test_plan_uses_ltm_endpoint():
    server, endpoint = _start_server()
    record = {
        "task_context": {"query": "example"},
        "execution_trace": {},
        "outcome": {"success": True},
    }
    requests.post(f"{endpoint}/memory", json={"record": record})

    agent = SupervisorAgent(ltm_endpoint=endpoint, retrieval_limit=1)
    plan = agent.plan_research_task("example")

    assert plan["context"]
    server.httpd.shutdown()


def test_plan_handles_no_memories():
    server, endpoint = _start_server()
    agent = SupervisorAgent(ltm_endpoint=endpoint)
    plan = agent.plan_research_task("missing")
    assert plan["context"] == []
    server.httpd.shutdown()


def test_valid_plan_fixture_passes_schema():
    agent = SupervisorAgent()
    path = Path("tests/fixtures/valid_supervisor_plan.yaml")
    yaml_text = path.read_text(encoding="utf-8")
    plan = agent.parse_plan(yaml_text)
    assert plan["query"] == "sample"


def test_invalid_plan_fixture_fails_schema():
    agent = SupervisorAgent()
    path = Path("tests/fixtures/invalid_supervisor_plan.yaml")
    yaml_text = path.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        agent.parse_plan(yaml_text)


def test_memories_scored_by_relevance():
    server, endpoint = _start_server()
    record_a = {
        "task_context": {"query": "example"},
        "execution_trace": {},
        "outcome": {"success": True},
    }
    record_b = {
        "task_context": {"query": "unrelated"},
        "execution_trace": {},
        "outcome": {"success": True},
    }
    requests.post(f"{endpoint}/memory", json={"record": record_a})
    requests.post(f"{endpoint}/memory", json={"record": record_b})

    agent = SupervisorAgent(ltm_endpoint=endpoint, retrieval_limit=2)
    plan = agent.plan_research_task("example")
    scores = [m.get("relevance") for m in plan["context"]]
    assert scores == sorted(scores, reverse=True)
    server.httpd.shutdown()


def test_plan_template_applied_when_enabled():
    server, endpoint = _start_server()
    template_plan = {
        "query": "example",
        "graph": {
            "nodes": [
                {"id": "research_0", "agent": "WebResearcher", "topic": "example"},
                {"id": "analysis", "agent": "Supervisor", "task": "analyze"},
            ],
            "edges": [
                {"from": "research_0", "to": "analysis"},
            ],
        },
    }
    record = {
        "task_context": {"query": "example", "plan": template_plan},
        "execution_trace": {},
        "outcome": {"success": True},
    }
    requests.post(f"{endpoint}/memory", json={"record": record})

    agent_plain = SupervisorAgent(ltm_endpoint=endpoint, use_plan_templates=False)
    plain = agent_plain.plan_research_task("example")

    agent_templ = SupervisorAgent(ltm_endpoint=endpoint, use_plan_templates=True)
    templ = agent_templ.plan_research_task("example")

    assert plain["graph"] != template_plan["graph"]
    assert templ["graph"] == template_plan["graph"]
    server.httpd.shutdown()
