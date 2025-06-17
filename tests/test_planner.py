import pytest

from agents import planner as planner_mod
from agents.planner import PlannerAgent
from engine.state import State

pytestmark = pytest.mark.core


class DummyGraphState:
    def __init__(self, data=None):
        self.data = data or {}

    def update(self, other):
        self.data.update(other)


class DummyResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_analyze_query_returns_state(monkeypatch):
    monkeypatch.setattr(
        planner_mod.requests, "get", lambda *a, **k: DummyResp({"results": []})
    )
    agent = PlannerAgent()
    agent.plan_schema = {}
    state = agent.analyze_query("What is AI?")
    assert isinstance(state, State)
    assert state.data["initial_query"] == "What is AI?"


def test_planner_node_updates_graph_state(monkeypatch):
    monkeypatch.setattr(
        planner_mod.requests, "get", lambda *a, **k: DummyResp({"results": []})
    )
    agent = PlannerAgent()
    agent.plan_schema = {}
    gs = DummyGraphState({"query": "Example query"})
    result = agent(gs)
    assert isinstance(result.data.get("state"), State)
    assert result.data["state"].data["initial_query"] == "Example query"


def test_task_allocation_balances_load(monkeypatch):
    def fake_get(*args, **kwargs):
        data = {
            "results": [
                {
                    "agent_id": "A1",
                    "reputation_vector": {"accuracy": 0.8, "token_cost": 1},
                },
                {
                    "agent_id": "A2",
                    "reputation_vector": {"accuracy": 0.8, "token_cost": 1},
                },
            ]
        }
        return DummyResp(data)

    monkeypatch.setattr(planner_mod.requests, "get", fake_get)
    agent = PlannerAgent(available_agents=["A1", "A2"])
    agent.plan_schema = {}
    plan = agent.plan_research_task("Topic1 vs Topic2")
    assignments = [
        n["agent"] for n in plan["graph"]["nodes"] if n["agent"] != "Supervisor"
    ]
    assert assignments.count("A1") == 1
    assert assignments.count("A2") == 1


def test_plan_yaml_roundtrip():
    agent = PlannerAgent()
    agent.plan_schema = {}
    plan = agent.plan_research_task("Example")
    yaml_text = agent.format_plan_as_yaml(plan)
    parsed = agent.parse_plan(yaml_text)
    assert parsed == plan


def test_planner_uses_reputation_api(monkeypatch):
    def fake_get(*args, **kwargs):
        data = {
            "results": [
                {
                    "agent_id": "A1",
                    "reputation_vector": {"accuracy": 0.9, "token_cost": 2},
                },
                {
                    "agent_id": "A2",
                    "reputation_vector": {"accuracy": 0.6, "token_cost": 1},
                },
            ]
        }
        return DummyResp(data)

    monkeypatch.setattr(planner_mod.requests, "get", fake_get)
    agent = PlannerAgent(available_agents=["A1", "A2"])
    agent.plan_schema = {}
    plan = agent.plan_research_task("Example")
    assigned = [
        n["agent"] for n in plan["graph"]["nodes"] if n["agent"] != "Supervisor"
    ][0]
    assert assigned == "A2"
