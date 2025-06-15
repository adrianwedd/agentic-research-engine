from __future__ import annotations

import asyncio
import time
import tracemalloc

from engine.orchestration_engine import GraphState, OrchestrationEngine


def build_sample_engine() -> OrchestrationEngine:
    eng = OrchestrationEngine()
    for i in range(5):

        def make_node(idx: int):
            def node(state: GraphState) -> GraphState:
                state.update({f"n{idx}": True})
                return state

            return node

        eng.add_node(f"n{i}", make_node(i))
        if i > 0:
            eng.add_edge(f"n{i-1}", f"n{i}")
    return eng


def benchmark_dynamic(iterations: int = 100) -> tuple[float, int]:
    start_time = time.perf_counter()
    tracemalloc.start()
    for _ in range(iterations):
        eng = build_sample_engine()
        asyncio.run(eng.run_async(GraphState()))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return time.perf_counter() - start_time, peak


def benchmark_compiled(iterations: int = 100) -> tuple[float, int]:
    eng = build_sample_engine()
    eng.build()
    start_time = time.perf_counter()
    tracemalloc.start()
    for _ in range(iterations):
        asyncio.run(eng.run_async(GraphState()))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return time.perf_counter() - start_time, peak


def build_hybrid_engine() -> OrchestrationEngine:
    """Create an engine with a compiled subgraph reused at runtime."""

    # subgraph that will be compiled once
    subgraph = OrchestrationEngine()
    for i in range(3):

        def make_node(idx: int):
            def node(state: GraphState) -> GraphState:
                state.update({f"s{idx}": True})
                return state

            return node

        subgraph.add_node(f"s{i}", make_node(i))
        if i > 0:
            subgraph.add_edge(f"s{i-1}", f"s{i}")
    subgraph.build()

    # top level engine that calls the compiled subgraph dynamically
    eng = OrchestrationEngine()

    async def call_subgraph(state: GraphState) -> GraphState:
        return await subgraph.run_async(state)

    eng.add_node("start", lambda state: state)
    eng.add_node("subgraph", call_subgraph)
    eng.add_node("end", lambda state: state)
    eng.add_edge("start", "subgraph")
    eng.add_edge("subgraph", "end")
    return eng


def benchmark_hybrid(iterations: int = 100) -> tuple[float, int]:
    """Benchmark a dynamic engine that reuses a compiled subgraph."""

    eng = build_hybrid_engine()
    eng.build()
    start_time = time.perf_counter()
    tracemalloc.start()
    for _ in range(iterations):
        asyncio.run(eng.run_async(GraphState()))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return time.perf_counter() - start_time, peak


if __name__ == "__main__":
    dyn_time, dyn_mem = benchmark_dynamic()
    comp_time, comp_mem = benchmark_compiled()
    hybrid_time, hybrid_mem = benchmark_hybrid()
    print(f"Dynamic build+run: {dyn_time:.4f}s, peak {dyn_mem} bytes")
    print(f"Compiled run: {comp_time:.4f}s, peak {comp_mem} bytes")
    print(f"Hybrid run:   {hybrid_time:.4f}s, peak {hybrid_mem} bytes")
