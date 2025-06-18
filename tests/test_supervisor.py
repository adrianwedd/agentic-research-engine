from pathlib import Path
from threading import Thread

import pytest
import requests

from agents.supervisor import SupervisorAgent
from engine.state import State
from services.ltm_service import (
    EpisodicMemoryService,
    InMemoryStorage,
    ProceduralMemoryService,
)
from services.ltm_service.api import LTMService, LTMServiceServer
from services.tool_registry import create_default_registry

pytestmark = pytest.mark.core


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
    assert state.data["initial_query"] == "What is AI?"


def test_supervisor_node_updates_graph_state():
    agent = SupervisorAgent()
    gs = DummyGraphState({"query": "Example query"})
    result = agent(gs)
    assert isinstance(result.data.get("state"), State)
    assert result.data["state"].data["initial_query"] == "Example query"


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
    assert result.data["state"].data["initial_query"] == "spaced query"


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

    registry = create_default_registry()
    agent = SupervisorAgent(
        ltm_endpoint=endpoint, retrieval_limit=1, tool_registry=registry
    )
    plan = agent.plan_research_task("example")

    assert plan["context"] == []
    server.httpd.shutdown()


def test_plan_uses_ltm_endpoint_authorized():
    server, endpoint = _start_server()
    record = {
        "task_context": {"query": "example"},
        "execution_trace": {},
        "outcome": {"success": True},
    }
    requests.post(f"{endpoint}/memory", json={"record": record})

    registry = create_default_registry()
    func = registry.get_tool("MemoryManager", "retrieve_memory")
    registry.register_tool(
        "retrieve_memory",
        func,
        allowed_roles=["MemoryManager", "Supervisor"],
    )
    agent = SupervisorAgent(
        ltm_endpoint=endpoint,
        retrieval_limit=1,
        tool_registry=registry,
    )
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


def test_json_schema_validation_rejects_bad_plan():
    agent = SupervisorAgent()
    agent.plan_schema = {}
    bad = {
        "query": "q",
        "context": [],
        "graph": {"nodes": [{"id": "n1"}], "edges": []},
        "evaluation": {},
    }
    with pytest.raises(ValueError):
        agent.validate_plan(bad)


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

    agent_default = SupervisorAgent(ltm_endpoint=endpoint)
    templ = agent_default.plan_research_task("example")

    assert templ["graph"] == template_plan["graph"]
    server.httpd.shutdown()


def test_skill_based_agent_selection():
    skills = {"A1": ["transformer", "lstm"], "A2": ["finance"]}
    agent = SupervisorAgent(
        available_agents=["A1", "A2"],
        agent_skills=skills,
    )
    agent.plan_schema = {}
    plan = agent.plan_research_task("Transformer vs LSTM")
    agents = [n["agent"] for n in plan["graph"]["nodes"] if n["agent"] != "Supervisor"]
    assert all(a == "A1" for a in agents)


def test_specialist_routing_from_procedural_memory(caplog):
    pm = ProceduralMemoryService(InMemoryStorage())
    pm.register_agent("A", domains=["legal"], success_rate=0.9)
    pm.register_agent("B", domains=["compliance"], success_rate=0.8)
    ltm = LTMService(EpisodicMemoryService(InMemoryStorage()), procedural_memory=pm)
    agent = SupervisorAgent(
        available_agents=["Generalist", "A", "B"],
        ltm_service=ltm,
        procedural_memory=pm,
    )
    agent.plan_schema = {}
    with caplog.at_level("INFO"):
        plan = agent.plan_research_task("legal compliance")
    node_agent = next(
        n["agent"]
        for n in plan["graph"]["nodes"]
        if n["agent"] not in {"Supervisor", "CitationAgent"}
    )
    assert node_agent == "A"
    assert any("agent_selection" in r.message for r in caplog.records)


def test_fallback_to_generalist():
    pm = ProceduralMemoryService(InMemoryStorage())
    pm.register_agent("A", domains=["legal"], success_rate=0.9)
    ltm = LTMService(EpisodicMemoryService(InMemoryStorage()), procedural_memory=pm)
    agent = SupervisorAgent(
        available_agents=["Generalist", "A"],
        ltm_service=ltm,
        procedural_memory=pm,
    )
    agent.plan_schema = {}
    plan = agent.plan_research_task("astronomy")
    node_agent = next(
        n["agent"]
        for n in plan["graph"]["nodes"]
        if n["agent"] not in {"Supervisor", "CitationAgent"}
    )
    assert node_agent == "Generalist"


def test_plan_includes_citation_agent():
    agent = SupervisorAgent()
    agent.plan_schema = {}
    plan = agent.plan_research_task("Example topic")
    nodes = plan["graph"]["nodes"]
    assert nodes[-1]["agent"] == "CitationAgent"
    assert {"from": "synthesis", "to": "citation"} in plan["graph"]["edges"]


def test_plan_contains_spatio_temporal_params():
    agent = SupervisorAgent()
    plan = agent.plan_research_task("Flooding in Europe from 2000 to 2010")
    assert plan.get("time_range") == {"valid_from": 2000, "valid_to": 2010}
    assert plan.get("bbox") == [-10.0, 35.0, 30.0, 60.0]
