import asyncio

import pytest
from pydantic import ValidationError

from engine.collaboration.group_chat import DynamicGroupChat, GroupChatManager
from engine.collaboration.message_protocol import ChatMessage
from engine.state import State

pytestmark = pytest.mark.core


def test_lost_message_triggers_retry(monkeypatch):
    attempts = []

    def agent_a(messages, state, scratchpad):
        # record attempts; resend if no reply
        attempt = state.data.get("attempt", 0)
        if attempt < 2:
            state.update({"attempt": attempt + 1})
            attempts.append(attempt + 1)
            return {"content": "ping", "recipient": "B"}
        return {"content": "FINISH", "type": "finish"}

    def agent_b(messages, state, scratchpad):
        if messages:
            state.update({"received": messages[0]["content"]})
            return {"content": "FINISH", "type": "finish"}
        return ""

    manager = GroupChatManager({"A": agent_a, "B": agent_b}, max_turns=5)
    dropped = True
    original_post = manager.chat.post_message

    def drop_first(sender, content, *, message_type="message", recipient=None):
        nonlocal dropped
        if dropped:
            dropped = False
            # simulate lost message by not delivering
            return None
        return original_post(
            sender, content, message_type=message_type, recipient=recipient
        )

    monkeypatch.setattr(manager.chat, "post_message", drop_first)

    state = asyncio.run(manager.run(State()))

    assert attempts == [1, 2]
    assert state.data.get("received") == "ping"


def test_out_of_order_message_delivery():
    chat = DynamicGroupChat({})
    chat.facilitate_team_collaboration(["A", "B"], {})
    chat.post_message("A", "1", recipient="B")
    chat.post_message("A", "2", recipient="B")
    chat.inboxes["B"][-2], chat.inboxes["B"][-1] = (
        chat.inboxes["B"][-1],
        chat.inboxes["B"][-2],
    )
    msgs = chat.get_messages("B")
    assert [m["content"] for m in msgs] == ["2", "1"]


def test_malformed_message_rejected():
    with pytest.raises(ValidationError):
        ChatMessage(sender="A", content=None)
