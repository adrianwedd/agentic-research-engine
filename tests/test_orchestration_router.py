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
from engine.routing import RoutingError, make_cosc_router, make_status_router


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


def test_conditional_router_executes_verifier():
    importlib.reload(trace)
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    engine = create_orchestration_engine()

    def start(state: GraphState, scratchpad: dict) -> GraphState:
        state.data.setdefault("order", []).append("Start")
        return state

    def verifier(state: GraphState, scratchpad: dict) -> GraphState:
        state.data["order"].append("Verifier")
        state.data["status"] = "approved"
        return state

    def complete(state: GraphState, scratchpad: dict) -> GraphState:
        state.data["order"].append("Complete")
        return state

    engine.add_node("Start", start)
    engine.add_node("Verifier", verifier)
    engine.add_node("Complete", complete)

    router = make_status_router(
        {
            "requires_verification": "Verifier",
            "approved": "Complete",
        }
    )

    engine.add_router("Start", router)
    engine.add_edge("Verifier", "Complete")

    state = GraphState(data={"status": "requires_verification"})

    result = asyncio.run(engine.run_async(state))

    assert result["data"]["order"] == ["Start", "Verifier", "Complete"]
    assert any(
        s.name == "route" and s.attributes["node"] == "Start" for s in exporter.spans
    )
    assert any(
        s.name == "edge"
        and s.attributes["from"] == "Start"
        and s.attributes["to"] == "Verifier"
        for s in exporter.spans
    )
    importlib.reload(trace)


def test_conditional_router_invalid_status_raises():
    engine = create_orchestration_engine()

    def start(state: GraphState, scratchpad: dict) -> GraphState:
        state.data.setdefault("order", []).append("Start")
        return state

    engine.add_node("Start", start)

    router = make_status_router({"requires_verification": "Verifier"})
    engine.add_router("Start", router)

    state = GraphState(data={"status": "unknown"})

    with pytest.raises(RoutingError):
        asyncio.run(engine.run_async(state))


def test_cosc_router_routes_for_retry():
    importlib.reload(trace)
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    engine = create_orchestration_engine()

    order: list[str] = []

    def researcher(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Researcher")
        return state

    def evaluator(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Evaluator")
        if state.retry_count == 0:
            state.evaluator_feedback = {"overall_score": 0.2}
        else:
            state.evaluator_feedback = {"overall_score": 0.8}
        return state

    def complete(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Complete")
        return state

    engine.add_node("Researcher", researcher)
    engine.add_node("Evaluator", evaluator)
    engine.add_node("Complete", complete)

    engine.add_edge("Researcher", "Evaluator")
    router = make_cosc_router(
        retry_node="Researcher",
        pass_node="Complete",
        max_retries=2,
        score_threshold=0.5,
    )
    engine.add_router("Evaluator", router)

    result = asyncio.run(engine.run_async(GraphState()))

    assert order == ["Researcher", "Evaluator", "Researcher", "Evaluator", "Complete"]
    assert result.retry_count == 1
    assert any(
        s.name == "state.update" and s.attributes.get("keys") == "retry_count"
        for s in exporter.spans
    )
    importlib.reload(trace)


def test_cosc_router_stops_after_max_retries():
    engine = create_orchestration_engine()

    order: list[str] = []

    def researcher(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Researcher")
        return state

    def evaluator(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Evaluator")
        state.evaluator_feedback = {"overall_score": 0.1}
        return state

    def abort(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Abort")
        return state

    engine.add_node("Researcher", researcher)
    engine.add_node("Evaluator", evaluator)
    engine.add_node("Abort", abort)

    engine.add_edge("Researcher", "Evaluator")
    router = make_cosc_router(
        retry_node="Researcher",
        pass_node="Abort",
        max_retries=1,
        score_threshold=0.5,
        fail_node="Abort",
    )
    engine.add_router("Evaluator", router)

    result = asyncio.run(engine.run_async(GraphState()))

    assert order == ["Researcher", "Evaluator", "Researcher", "Evaluator", "Abort"]
    assert result.retry_count == 1


def test_cosc_loop_terminates_after_three_retries():
    engine = create_orchestration_engine()

    order: list[str] = []

    def researcher(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Researcher")
        return state

    def evaluator(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Evaluator")
        state.evaluator_feedback = {"overall_score": 0.0}
        return state

    def failure(state: GraphState, scratchpad: dict) -> GraphState:
        order.append("Failure")
        return state

    engine.add_node("Researcher", researcher)
    engine.add_node("Evaluator", evaluator)
    engine.add_node("Failure", failure)

    engine.add_edge("Researcher", "Evaluator")
    router = make_cosc_router(
        retry_node="Researcher",
        pass_node="Failure",
        max_retries=3,
        score_threshold=0.5,
        fail_node="Failure",
    )
    engine.add_router("Evaluator", router)

    result = asyncio.run(engine.run_async(GraphState()))

    assert order == [
        "Researcher",
        "Evaluator",
        "Researcher",
        "Evaluator",
        "Researcher",
        "Evaluator",
        "Researcher",
        "Evaluator",
        "Failure",
    ]
    assert result.retry_count == 3
