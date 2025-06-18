from __future__ import annotations

import importlib
import threading
import time

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from playwright.sync_api import sync_playwright

from engine.orchestration_engine import GraphState, create_orchestration_engine
from services.tracing import GraphTraceExporter, create_app


@pytest.fixture(scope="module")
def dashboard_server(tmp_path_factory):
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

    dashboard_path = str(tmp_path_factory.mktemp("dash"))
    from shutil import copytree

    copytree("dashboard", dashboard_path, dirs_exist_ok=True)

    app = create_app(exporter, dashboard_path=dashboard_path)

    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=8787, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1)
    yield exporter
    server.should_exit = True
    thread.join()


def test_dashboard_loads_nodes_and_edges(dashboard_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://127.0.0.1:8787/dashboard/")
        page.wait_for_function("window.__GRAPH_DATA !== undefined")
        nodes = page.evaluate("window.__GRAPH_DATA.nodes.length")
        edges = page.evaluate("window.__GRAPH_DATA.edges.length")
        assert nodes == 2
        assert edges == 1
        browser.close()
