import asyncio
import importlib

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from engine.orchestration_engine import GraphState, create_orchestration_engine
from engine.routing import make_edge_type_router

pytestmark = pytest.mark.core


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - interface req
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:  # pragma: no cover
        return True


def test_sequential_execution_and_spans():
    importlib.reload(trace)
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    order = []

    def node_a(state: GraphState) -> GraphState:
        order.append("A")
        state.update({"a": 1})
        return state

    def node_b(state: GraphState) -> GraphState:
        order.append("B")
        state.update({"b": state.data.get("a")})
        return state

    engine = create_orchestration_engine()
    engine.add_node("A", node_a)
    engine.add_node("B", node_b)
    engine.add_edge("A", "B")

    result = asyncio.run(engine.run_async(GraphState()))
    assert result.data["b"] == 1
    assert order == ["A", "B"]

    span_names = [span.name for span in exporter.spans]
    assert "node:A" in span_names
    assert "node:B" in span_names
    node_a_span = next(s for s in exporter.spans if s.name == "node:A")
    node_b_span = next(s for s in exporter.spans if s.name == "node:B")
    assert "state_in" in node_a_span.attributes
    assert "state_out" in node_a_span.attributes
    assert "state_in" in node_b_span.attributes
    assert "state_out" in node_b_span.attributes
    assert any(
        s.name == "state.update" and s.attributes["action"] == "update"
        for s in exporter.spans
    )
    assert any(
        span.name == "edge"
        and span.attributes["from"] == "A"
        and span.attributes["to"] == "B"
        for span in exporter.spans
    )
    importlib.reload(trace)


def test_export_dot_outputs_valid_graph():
    engine = create_orchestration_engine()

    engine.add_node("A", lambda s: s)
    engine.add_node("B", lambda s: s)
    engine.add_edge("A", "B")

    engine.build()
    dot = engine.export_dot()

    expected = "\n".join(
        [
            "digraph Orchestration {",
            '  "A";',
            '  "B";',
            '  "A" -> "B";',
            "}",
        ]
    )

    assert dot == expected


def test_typed_edges_routing_and_lookup():
    engine = create_orchestration_engine()

    def start(state: GraphState) -> GraphState:
        return state

    def node_b(state: GraphState) -> GraphState:
        state.update({"dest": "B"})
        return state

    def node_c(state: GraphState) -> GraphState:
        state.update({"dest": "C"})
        return state

    engine.add_node("Start", start)
    engine.add_node("B", node_b)
    engine.add_node("C", node_c)

    engine.add_edge("Start", "B", edge_type="success")
    engine.add_edge("Start", "C", edge_type="fail")

    router = make_edge_type_router(engine, "Start", state_key="path")
    engine.add_router("Start", router)

    state = GraphState(data={"path": "fail"})
    result = asyncio.run(engine.run_async(state))

    assert result.data["dest"] == "C"
    assert engine.get_edges("Start", "success")[0].end == "B"
    engine.build()
    dot = engine.export_dot()
    assert '"Start" -> "B" [label="success"];' in dot
