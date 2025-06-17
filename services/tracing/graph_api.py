from __future__ import annotations

"""Expose execution graph derived from OpenTelemetry spans."""

import json
from typing import Any, Dict, List, Set

from fastapi import FastAPI, HTTPException
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


def _extract_node_states(spans: List[ReadableSpan]) -> Dict[str, Dict[str, Any]]:
    """Return mapping of node name to parsed ``state_out`` JSON."""
    states: Dict[str, Dict[str, Any]] = {}
    for span in spans:
        if span.name.startswith("node:") and "state_out" in span.attributes:
            node = span.name.split(":", 1)[1]
            try:
                states[node] = json.loads(span.attributes["state_out"])
            except Exception:
                states[node] = {}
    return states


def spans_to_graph(spans: List[ReadableSpan]) -> Dict[str, List[Dict[str, Any]]]:
    """Convert spans to a graph representation with node metadata."""
    states = _extract_node_states(spans)
    nodes_set: Set[str] = set(states)
    edges: List[Dict[str, Any]] = []
    for span in spans:
        if span.name.startswith("node:"):
            node = span.name.split(":", 1)[1]
            nodes_set.add(node)
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

    nodes: List[Dict[str, Any]] = []
    for name in sorted(nodes_set):
        state = states.get(name, {})
        conf = state.get("scratchpad", {}).get("confidence")
        intent = state.get("scratchpad", {}).get("intent")
        nodes.append({"id": name, "confidence": conf, "intent": intent})

    return {"nodes": nodes, "edges": edges}


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
    def get_graph() -> Dict[str, List[Dict[str, Any]]]:
        return spans_to_graph(exporter.spans)

    @app.get("/belief/{node}/{key}")
    def get_belief(node: str, key: str) -> Dict[str, Any]:
        states = _extract_node_states(exporter.spans)
        state = states.get(node)
        if not state:
            raise HTTPException(status_code=404, detail="node not found")
        value = None
        if key in state.get("data", {}):
            value = state["data"][key]
        elif key in state.get("scratchpad", {}):
            value = state["scratchpad"][key]
        return {"value": value, "history": state.get("history", [])}

    return app
