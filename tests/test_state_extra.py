import pytest

from engine.state import State

pytestmark = pytest.mark.core


def test_getitem_returns_attribute():
    state = State(data={"foo": 1})
    assert state["data"] == {"foo": 1}


def test_update_records_history_order():
    state = State()
    state.update({"a": 1})
    state.update({"b": 2})
    assert state.history == [
        {"action": "update", "data": {"a": 1}},
        {"action": "update", "data": {"b": 2}},
    ]


def test_add_message_appends():
    state = State()
    state.add_message({"content": "hi"})
    state.add_message({"content": "there"})
    assert state.messages == [
        {"content": "hi"},
        {"content": "there"},
    ]
    assert state.history[-1] == {
        "action": "add_message",
        "message": {"content": "there"},
    }
