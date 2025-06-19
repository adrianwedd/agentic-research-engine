from unittest import mock

from tools import adapters


def test_execute_dispatches():
    call = adapters.ToolCall(name="web.search", args={"query": "ai"})
    fake = mock.Mock(return_value=[{"url": "x"}])
    adapters._REGISTRY["web.search"] = fake
    result = adapters.execute(call)
    fake.assert_called_once_with(query="ai")
    assert result == [{"url": "x"}]


def test_entrypoint_loading(monkeypatch):
    class EP:
        def __init__(self, name):
            self.name = name

        def load(self):
            return lambda **_: "ok"

    monkeypatch.setattr(
        adapters.metadata,
        "entry_points",
        lambda: {"research_agent.tools": [EP("dummy")]},
    )
    adapters._REGISTRY.clear()
    adapters._load_entrypoints()
    assert "dummy" in adapters._REGISTRY
