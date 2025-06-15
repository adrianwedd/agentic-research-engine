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
