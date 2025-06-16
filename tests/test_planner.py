import pytest

from agents.planner import PlannerAgent
from engine.state import State

pytestmark = pytest.mark.core


class DummyGraphState:
    def __init__(self, data=None):
        self.data = data or {}

    def update(self, other):
        self.data.update(other)


def test_analyze_query_returns_state():
    agent = PlannerAgent()
    state = agent.analyze_query("What is AI?")
    assert isinstance(state, State)
    assert state.data["initial_query"] == "What is AI?"


def test_planner_node_updates_graph_state():
    agent = PlannerAgent()
    gs = DummyGraphState({"query": "Example query"})
    result = agent(gs)
    assert isinstance(result.data.get("state"), State)
    assert result.data["state"].data["initial_query"] == "Example query"


def test_task_allocation_uses_available_agents():
    agent = PlannerAgent(available_agents=["A1", "A2"])
    plan = agent.plan_research_task("Topic1 vs Topic2")
    nodes = {
        n["topic"]: n["agent"]
        for n in plan["graph"]["nodes"]
        if n["agent"] != "Supervisor"
    }
    assert nodes.get("Topic1") == "A1"
    assert nodes.get("Topic2") == "A2"


def test_plan_yaml_roundtrip():
    agent = PlannerAgent()
    plan = agent.plan_research_task("Example")
    yaml_text = agent.format_plan_as_yaml(plan)
    parsed = agent.parse_plan(yaml_text)
    assert parsed == plan
