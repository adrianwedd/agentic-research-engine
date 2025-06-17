import asyncio

import pytest

from engine.collaboration.group_chat import DynamicGroupChat
from engine.state import State

pytestmark = pytest.mark.core


@pytest.mark.asyncio
async def test_concurrent_scratchpad_updates():
    state = State()
    chat = DynamicGroupChat({}, enable_lock=True)
    chat.bind_state(state)
    chat.write_scratchpad("count", 0)

    async def worker():
        await asyncio.sleep(0)
        chat.update_scratchpad("count", lambda v: (v or 0) + 1)

    await asyncio.gather(*(worker() for _ in range(200)))

    assert chat.read_scratchpad("count") == 200
    assert state.scratchpad["count"] == 200
