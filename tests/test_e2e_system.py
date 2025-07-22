import importlib
import json
import os
from typing import Any

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from agents.web_researcher import WebResearcherAgent
from engine.orchestration_engine import GraphState, create_orchestration_engine
from tests.benchmarks.integration_harness import IntegrationTestHarness

pytestmark = pytest.mark.integration

os.environ.setdefault("PYTEST_DISABLE_RATE_LIMIT", "1")


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans) -> SpanExportResult:
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - interface req
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:  # pragma: no cover
        return True


def _make_registry(search_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "web_search": lambda q: search_results,
        "summarize": lambda text: "summary",
        "pdf_extract": None,
        "html_scraper": None,
        "assess_source": lambda url: 1.0,
    }


@pytest.mark.asyncio
async def test_full_request_to_execution_trace():
    importlib.reload(trace)
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    registry = _make_registry([{"url": "http://example.com", "title": "Ex"}])
    researcher = WebResearcherAgent(registry)

    def supervisor_node(state: GraphState, _: dict) -> GraphState:
        state.update({"sub_task": "find location of OpenAI"})
        return state

    engine = create_orchestration_engine()
    engine.add_node("Supervisor", supervisor_node)
    engine.add_node("WebResearcher", researcher)
    engine.add_edge("Supervisor", "WebResearcher")

    result = await engine.run_async(GraphState())
    assert result.data["research_result"]["sources"]

    span_names = [s.name for s in exporter.spans]
    assert "task" in span_names
    assert "node:Supervisor" in span_names
    assert "node:WebResearcher" in span_names
    assert any(s.name == "tool_call" for s in exporter.spans)
    assert len({s.context.trace_id for s in exporter.spans}) == 1
    importlib.reload(trace)


def test_foundational_benchmark_run():
    dataset = "benchmarks/browsecomp/dataset_v1.json"
    with open(dataset, "r", encoding="utf-8") as f:
        cases = json.load(f)
    answers = {c["question"]: c["answer"] for c in cases}

    def agent(question: str) -> dict:
        return {"answer": answers.get(question, "")}

    harness = IntegrationTestHarness(dataset, timeout=1)
    report = harness.run(agent)
    assert report["total_cases"] == len(cases)
    assert report["passed"] == len(cases)
    assert report["pass_rate"] == 1.0
    assert report["average_time"] >= 0


@pytest.mark.asyncio
async def test_dynamic_workflow_routing():
    registry_hits = _make_registry([{"url": "http://example.com", "title": "Ex"}])
    registry_empty = _make_registry([])

    def summarize_node(state: GraphState, _: dict) -> GraphState:
        state.update({"summary": True})
        return state

    def router(state: GraphState) -> str:
        if state.data.get("research_result", {}).get("sources"):
            return "Summarize"
        return "End"

    # results case
    eng = create_orchestration_engine()
    eng.add_node("Research", WebResearcherAgent(registry_hits))
    eng.add_node("Summarize", summarize_node)
    eng.add_node("End", lambda s, sp: s)
    eng.add_router("Research", router)
    eng.add_edge("Summarize", "End")

    result = await eng.run_async(
        GraphState(data={"sub_task": "topic"}), start_at="Research"
    )
    assert result.data.get("summary") is True

    # empty case
    eng2 = create_orchestration_engine()
    eng2.add_node("Research", WebResearcherAgent(registry_empty))
    eng2.add_node("Summarize", summarize_node)
    eng2.add_node("End", lambda s, sp: s)
    eng2.add_router("Research", router)
    eng2.add_edge("Summarize", "End")

    result2 = await eng2.run_async(
        GraphState(data={"sub_task": "topic"}), start_at="Research"
    )
    assert "summary" not in result2.data
