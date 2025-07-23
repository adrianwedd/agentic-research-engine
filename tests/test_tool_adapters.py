from importlib import metadata, reload
from unittest import mock

from tools import adapters


def test_execute_dispatches():
    call = adapters.ToolCall(name="web.search", args={"query": "ai"})
    fake = mock.Mock(return_value=[{"url": "x"}])
    adapters._REGISTRY["web.search"] = fake
    result = adapters.execute(call)
    fake.assert_called_once_with(query="ai")
    assert result == [{"url": "x"}]


def dummy_plugin_tool():
    return "plugin"


def test_entrypoint_plugins_loaded(monkeypatch):
    ep = metadata.EntryPoint(
        name="dummy_plugin",
        value="tests.test_tool_adapters:dummy_plugin_tool",
        group="agentic_research_engine.tools",
    )

    def fake_entry_points(*args, **kwargs):  # pragma: no cover - deterministic
        return [ep] if kwargs.get("group") == ep.group else []

    monkeypatch.setattr(metadata, "entry_points", fake_entry_points)
    reload(adapters)

    call = adapters.ToolCall(name="dummy_plugin", args={})
    assert adapters.execute(call) == "plugin"
