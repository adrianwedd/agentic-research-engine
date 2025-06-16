from __future__ import annotations

import asyncio

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from engine.collaboration.group_chat import GroupChatManager
from engine.orchestration_engine import NodeType, OrchestrationEngine
from engine.state import State


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - not needed
        pass

    def force_flush(
        self, timeout_millis: int = 30_000
    ) -> bool:  # pragma: no cover - not needed
        return True


def test_task_span_contains_metrics():
    exporter = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.add_span_processor(SimpleSpanProcessor(exporter))

    async def agent_a(msgs, state):
        return {"content": "done", "type": "finish"}

    manager = GroupChatManager({"A": agent_a}, max_turns=1)

    engine = OrchestrationEngine()
    engine.add_node("chat", manager.run, node_type=NodeType.GROUP_CHAT_MANAGER)

    asyncio.run(engine.run_async(State()))

    task_span = next((s for s in exporter.spans if s.name == "task"), None)
    assert task_span is not None
    assert "total_messages_sent" in task_span.attributes
    assert "average_message_latency" in task_span.attributes
    assert "action_advancement_rate" in task_span.attributes
    assert "total_tokens_consumed" in task_span.attributes
    assert "tool_call_count" in task_span.attributes
    assert "self_correction_loops" in task_span.attributes
    assert "communication_overhead" in task_span.attributes
