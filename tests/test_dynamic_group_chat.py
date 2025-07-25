import pytest

from engine.collaboration.group_chat import DynamicGroupChat
from engine.state import State

pytestmark = pytest.mark.core


def test_message_passing():
    chat = DynamicGroupChat({})
    chat.facilitate_team_collaboration(["A", "B"], {})
    chat.post_message("A", "hello", message_type="question", recipient="B")
    msgs_b = chat.get_messages("B")
    assert msgs_b and msgs_b[-1]["content"] == "hello"
    assert msgs_b[-1]["type"] == "question"
    assert msgs_b[-1]["recipient"] == "B"


def test_shared_workspace():
    workspace = {}
    chat = DynamicGroupChat(workspace)
    chat.facilitate_team_collaboration(["A", "B"], {})
    chat.update_workspace("A", "note", "value")
    assert workspace["note"] == "value"


def test_scratchpad_binding_and_rw():
    state = State()
    chat = DynamicGroupChat({})
    chat.bind_state(state)
    chat.facilitate_team_collaboration(["A", "B"], {})
    chat.write_scratchpad("foo", "bar")
    assert chat.read_scratchpad("foo") == "bar"
    assert state.scratchpad["foo"] == "bar"
