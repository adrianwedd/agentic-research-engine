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


@pytest.mark.asyncio
async def test_concurrent_message_order():
    state = State()
    chat = DynamicGroupChat({}, enable_lock=True)
    chat.bind_state(state)

    async def worker(i: int) -> None:
        await asyncio.sleep(i * 0.001)
        chat.update_scratchpad("log", lambda v, idx=i: (v or []) + [f"msg {idx}"])

    await asyncio.gather(*(worker(i) for i in range(50)))

    assert chat.read_scratchpad("log") == [f"msg {i}" for i in range(50)]
    assert state.scratchpad["log"] == [f"msg {i}" for i in range(50)]
