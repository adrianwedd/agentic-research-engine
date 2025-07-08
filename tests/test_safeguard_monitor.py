import logging

import pytest

from engine.collaboration.group_chat import DynamicGroupChat
from services.policy_monitor import PolicyMonitor, PolicyViolation, set_monitor
from services.tool_registry import ToolRegistry


def dummy_tool():
    return "ok"


def test_blocked_tool_raises_and_logged(caplog):
    monitor = PolicyMonitor({"blocked_tools": ["dummy"]})
    set_monitor(monitor)
    registry = ToolRegistry()
    registry.register_tool("dummy", dummy_tool)
    caplog.set_level(logging.WARNING)
    with pytest.raises(PolicyViolation):
        registry.invoke("A", "dummy")
    assert any("blocked" in r.message for r in caplog.records)
    assert any(e["type"] == "tool" and not e["allowed"] for e in monitor.events)


def test_blocked_message_raises_and_logged(caplog):
    monitor = PolicyMonitor({"blocked_keywords": ["bad"]})
    set_monitor(monitor)
    chat = DynamicGroupChat({})
    caplog.set_level(logging.WARNING)
    chat.post_message("A", "hello")
    with pytest.raises(PolicyViolation):
        chat.post_message("A", "this is bad")
    assert any("blocked" in r.message for r in caplog.records)
    assert any(e["type"] == "message" and not e["allowed"] for e in monitor.events)
