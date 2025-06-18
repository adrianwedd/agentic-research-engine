from __future__ import annotations

import importlib

from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from engine.orchestration_engine import GraphState, create_orchestration_engine
from services.tracing import GraphTraceExporter, create_app


def test_graph_api_returns_graph():
    importlib.reload(trace)
    exporter = GraphTraceExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    engine = create_orchestration_engine()

    def node_a(state: GraphState, scratchpad: dict) -> GraphState:
        state.update({"a": 1})
        return state

    def node_b(state: GraphState, scratchpad: dict) -> GraphState:
        state.update({"b": state.data["a"]})
        return state

    engine.add_node("A", node_a)
    engine.add_node("B", node_b)
    engine.add_edge("A", "B")

    engine.run(GraphState())

    app = create_app(exporter)
    client = TestClient(app)
    resp = client.get("/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert {n["id"] for n in data["nodes"]} == {"A", "B"}
    assert any(e["from"] == "A" and e["to"] == "B" for e in data["edges"])


def test_graph_encodes_confidence_and_belief_provenance():
    importlib.reload(trace)
    exporter = GraphTraceExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    engine = create_orchestration_engine()

    def node_a(state: GraphState, scratchpad: dict) -> GraphState:
        scratchpad["confidence"] = 0.75
        scratchpad["intent"] = "B"
        state.update({"a": 1})
        return state

    def node_b(state: GraphState, scratchpad: dict) -> GraphState:
        return state

    engine.add_node("A", node_a)
    engine.add_node("B", node_b)
    engine.add_edge("A", "B")

    engine.run(GraphState())

    app = create_app(exporter)
    client = TestClient(app)

    data = client.get("/graph").json()
    node_a_data = next(n for n in data["nodes"] if n["id"] == "A")
    assert node_a_data["confidence"] == 0.75
    assert node_a_data["intent"] == "B"

    resp = client.get("/belief/A/confidence")
    assert resp.status_code == 200
    belief = resp.json()
    assert belief["value"] == 0.75
    assert belief["history"]

    resp = client.get("/belief/A/intent")
    assert resp.status_code == 200
    belief = resp.json()
    assert belief["value"] == "B"
    assert belief["history"]
