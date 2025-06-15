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
