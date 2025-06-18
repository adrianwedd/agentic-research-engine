from __future__ import annotations

"""Expose execution graph derived from OpenTelemetry spans."""

import asyncio
import json
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Set

if TYPE_CHECKING:  # pragma: no cover - for type hints
    from engine.orchestration_engine import GraphState as _GraphState  # noqa: F401
    from engine.orchestration_engine import OrchestrationEngine

try:  # optional dependency
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    from fastapi.staticfiles import StaticFiles
except Exception:  # pragma: no cover - fallback objects
    FastAPI = object
    HTTPException = Exception
    StreamingResponse = object
    StaticFiles = object

try:
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
except Exception:  # pragma: no cover - fallback classes
    ReadableSpan = object

    class SpanExporter:
        pass

    class SpanExportResult:
        SUCCESS = 0


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


def _span_to_dict(span: ReadableSpan) -> Dict[str, Any]:
    """Convert a ``ReadableSpan`` to a JSON-serializable dict."""
    return {
        "name": span.name,
        "start": span.start_time / 1e9,
        "end": span.end_time / 1e9,
        "attributes": dict(span.attributes),
    }


def spans_to_graph(spans: List[ReadableSpan]) -> Dict[str, List[Dict[str, Any]]]:
    """Convert spans to a graph representation with node metadata."""
    states = _extract_node_states(spans)
    nodes_set: Set[str] = set(states)
    node_times: Dict[str, Dict[str, float]] = {}
    edges: List[Dict[str, Any]] = []
    for span in spans:
        if span.name.startswith("node:"):
            node = span.name.split(":", 1)[1]
            nodes_set.add(node)
            node_times[node] = {
                "start": span.start_time / 1e9,
                "end": span.end_time / 1e9,
            }
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
        timing = node_times.get(name, {})
        nodes.append(
            {
                "id": name,
                "confidence": conf,
                "intent": intent,
                **timing,
            }
        )

    return {"nodes": nodes, "edges": edges}


class GraphTraceExporter(SpanExporter):
    """Collect spans in memory for graph extraction and streaming."""

    def __init__(self) -> None:
        self.spans: List[ReadableSpan] = []
        self.events: asyncio.Queue[ReadableSpan] = asyncio.Queue()

    def export(
        self, spans: List[ReadableSpan]
    ) -> SpanExportResult:  # pragma: no cover - OTLP interface
        self.spans.extend(spans)
        for span in spans:
            try:
                self.events.put_nowait(span)
            except Exception:
                pass
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - interface req
        self.spans.clear()

    def force_flush(
        self, timeout_millis: int = 30_000
    ) -> bool:  # pragma: no cover - interface req
        return True


def create_app(
    exporter: GraphTraceExporter,
    dashboard_path: str | None = None,
    engine: "OrchestrationEngine" | None = None,
) -> FastAPI:
    """Return a FastAPI app exposing the current execution graph."""

    app = FastAPI(title="Graph Trace API", version="1.0.0")

    @app.get("/graph")
    def get_graph() -> Dict[str, List[Dict[str, Any]]]:
        return spans_to_graph(exporter.spans)

    @app.get("/events")
    async def stream_events() -> StreamingResponse:
        async def generator() -> AsyncGenerator[str, None]:
            while True:
                span = await exporter.events.get()
                yield f"data: {json.dumps(_span_to_dict(span))}\n\n"

        return StreamingResponse(generator(), media_type="text/event-stream")

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

    if engine:

        @app.post("/simulate")
        async def run_simulation(payload: Dict[str, Any]) -> Dict[str, Any]:
            state_data = payload.get("state", {})
            plan = payload.get("plan")
            from engine.orchestration_engine import GraphState as RuntimeGraphState

            state: _GraphState = RuntimeGraphState.model_validate(state_data)
            if plan is not None:
                state.update({"plan": plan})
            result, metrics = await engine.run_sandbox_async(state)
            return {"state": result.model_dump(), "metrics": metrics}

        from services.tracing.simulations import load_simulation

        @app.get("/compare/{run_id}")
        def compare(run_id: str) -> Dict[str, Any]:
            try:
                sim = load_simulation(run_id)
            except Exception as exc:
                raise HTTPException(status_code=404, detail=str(exc))
            return {
                "live": engine.last_metrics or {},
                "simulation": sim.get("metrics", {}),
            }

        @app.get("/autonomy")
        def get_autonomy() -> Dict[str, str]:
            level = (
                engine.current_state.autonomy_level
                if engine.current_state is not None
                else engine.default_autonomy_level
            )
            return {"level": level}

        @app.post("/autonomy")
        def set_autonomy(payload: Dict[str, str]) -> Dict[str, str]:
            level_str = payload.get("level")
            try:
                from engine.state import State as RuntimeState

                level = RuntimeState.AutonomyLevel(level_str)
            except Exception:
                raise HTTPException(status_code=400, detail="invalid level")
            engine.set_autonomy_level(level)
            return {"level": level}

        @app.post("/pause")
        def pause() -> Dict[str, str]:
            engine.pause()
            return {"status": "PAUSED"}

        @app.post("/resume")
        async def resume() -> Dict[str, Any]:
            result = await engine.resume_async()
            return {"state": result.model_dump()}

    if dashboard_path:
        app.mount(
            "/dashboard",
            StaticFiles(directory=dashboard_path, html=True),
            name="dashboard",
        )

    return app
