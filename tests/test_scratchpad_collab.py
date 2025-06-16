import pytest

from engine.collaboration.group_chat import DynamicGroupChat
from engine.state import State

pytestmark = pytest.mark.core


def test_shared_scratchpad_persistence_between_agents():
    state = State()
    chat = DynamicGroupChat({})
    chat.bind_state(state)
    chat.facilitate_team_collaboration(["A", "B"], {})

    # Agent A writes to the scratchpad
    chat.write_scratchpad("data", "value")
    assert state.scratchpad["data"] == "value"

    # Simulate persisting and restoring state between turns
    payload = state.to_json()
    restored = State.from_json(payload)
    chat.bind_state(restored)

    # Agent B reads the value and verifies it
    assert chat.read_scratchpad("data") == "value"
    assert restored.scratchpad["data"] == "value"

    # Ensure no other fields changed
    assert restored.data == {}
    assert restored.messages == []
    assert restored.history == []
    assert restored.status is None
