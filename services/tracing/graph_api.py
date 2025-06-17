from __future__ import annotations

"""Expose execution graph derived from OpenTelemetry spans."""

from typing import Dict, List, Set

from fastapi import FastAPI
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


def spans_to_graph(spans: List[ReadableSpan]) -> Dict[str, List[Dict]]:
    """Convert spans to a graph representation."""
    nodes: Set[str] = set()
    edges: List[Dict[str, object]] = []
    for span in spans:
        if span.name.startswith("node:"):
            node = span.name.split(":", 1)[1]
            nodes.add(node)
        elif span.name == "edge":
            start = span.attributes.get("from")
            end = span.attributes.get("to")
            if start and end:
                edges.append(
                    {
                        "from": str(start),
                        "to": str(end),
                        "type": span.attributes.get("type"),
                        "timestamp": span.start_time / 1e9,
                    }
                )
    return {"nodes": sorted(nodes), "edges": edges}


class GraphTraceExporter(SpanExporter):
    """Collect spans in memory for graph extraction."""

    def __init__(self) -> None:
        self.spans: List[ReadableSpan] = []

    def export(
        self, spans: List[ReadableSpan]
    ) -> SpanExportResult:  # pragma: no cover - OTLP interface
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - interface req
        self.spans.clear()

    def force_flush(
        self, timeout_millis: int = 30_000
    ) -> bool:  # pragma: no cover - interface req
        return True


def create_app(exporter: GraphTraceExporter) -> FastAPI:
    """Return a FastAPI app exposing the current execution graph."""

    app = FastAPI(title="Graph Trace API", version="1.0.0")

    @app.get("/graph")
    def get_graph() -> Dict[str, List[Dict]]:
        return spans_to_graph(exporter.spans)

    return app
