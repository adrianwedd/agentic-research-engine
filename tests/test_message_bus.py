import pytest

from engine.orchestration_engine import GraphState, create_orchestration_engine
from services import InMemoryMessageBus


@pytest.mark.asyncio
async def test_message_bus_event_delivery():
    bus = InMemoryMessageBus()
    received = []

    async def handler(data: bytes) -> None:
        received.append(data.decode())

    await bus.subscribe("t.events", handler)

    engine = create_orchestration_engine(message_bus=bus)

    def node_a(state: GraphState, _):
        state.update({"x": 1})
        return state

    engine.add_node("A", node_a)

    await engine.run_async(GraphState(), thread_id="t")

    assert received == ["start:A", "end:A", "complete"]


class FlakyBus(InMemoryMessageBus):
    def __init__(self):
        super().__init__()
        self.attempts = 0

    async def publish(self, subject: str, data: bytes) -> None:
        self.attempts += 1
        if self.attempts < 2:
            raise RuntimeError("boom")
        await super().publish(subject, data)


@pytest.mark.asyncio
async def test_message_bus_retry():
    bus = FlakyBus()
    received = []

    async def handler(data: bytes) -> None:
        received.append(data.decode())

    await bus.subscribe("t.events", handler)

    engine = create_orchestration_engine(message_bus=bus)
    engine.add_node("A", lambda s, _: s)

    await engine.run_async(GraphState(), thread_id="t")

    assert "complete" in received
    assert bus.attempts >= 2
