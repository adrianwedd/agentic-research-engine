import pytest

from agents.supervisor import State, SupervisorAgent


class DummyGraphState:
    def __init__(self, data=None):
        self.data = data or {}

    def update(self, other):
        self.data.update(other)


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
