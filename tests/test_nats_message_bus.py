import socket
import subprocess
import time

import pytest

from engine.orchestration_engine import GraphState, create_orchestration_engine
from services import NATSMessageBus


@pytest.fixture(scope="module")
def nats_server():
    port = 4223
    proc = subprocess.Popen(
        [
            "nats-server",
            "-p",
            str(port),
            "-DV",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    start = time.time()
    while True:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            if time.time() - start > 5:
                proc.terminate()
                raise RuntimeError("nats-server failed to start")
            time.sleep(0.1)
    yield f"nats://127.0.0.1:{port}"
    proc.terminate()
    proc.wait()


@pytest.mark.asyncio
async def test_nats_message_bus_event_delivery(nats_server):
    bus = NATSMessageBus(nats_server)
    await bus.connect()
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
    await bus.close()

    assert received == ["start:A", "end:A", "complete"]
