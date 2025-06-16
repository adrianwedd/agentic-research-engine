import asyncio

import pytest

from engine.collaboration.group_chat import GroupChatManager
from engine.state import State

pytestmark = pytest.mark.core


def test_group_chat_manager_message_passing():
    received_by_b = []

    def agent_a(messages, state):
        assert messages == []
        return "hello"

    def agent_b(messages, state):
        received_by_b.extend(messages)
        return {"content": "FINISH", "type": "finish"}

    manager = GroupChatManager({"A": agent_a, "B": agent_b}, max_turns=2)
    state = asyncio.run(manager.run(State()))

    assert any(m["content"] == "hello" for m in state.data["conversation"])
    assert received_by_b and received_by_b[0]["content"] == "hello"


def test_directed_question_routing():
    order = []

    def agent_a(messages, state):
        order.append("A")
        return {"content": "where are we?", "type": "question", "recipient": "B"}

    def agent_b(messages, state):
        order.append("B")
        assert messages and messages[0]["recipient"] == "B"
        return {"content": "FINISH", "type": "finish"}

    def agent_c(messages, state):
        order.append("C")
        return "noop"

    manager = GroupChatManager({"A": agent_a, "C": agent_c, "B": agent_b}, max_turns=3)
    state = asyncio.run(manager.run(State()))

    assert order == ["A", "B"]
    conv = state.data["conversation"]
    assert any(m.get("recipient") == "B" and m.get("type") == "question" for m in conv)


def test_group_chat_scratchpad_shared():
    def agent_a(messages, state):
        manager.chat.write_scratchpad("foo", "bar")
        return "continue"

    def agent_b(messages, state):
        seen = manager.chat.read_scratchpad("foo")
        state.update({"seen": seen})
        return {"content": "FINISH", "type": "finish"}

    manager = GroupChatManager({"A": agent_a, "B": agent_b}, max_turns=2)
    state = asyncio.run(manager.run(State()))

    assert state.scratchpad["foo"] == "bar"
    assert state.data["seen"] == "bar"
