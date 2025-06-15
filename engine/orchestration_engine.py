# P1-01: Implement Core LangGraph Orchestration Engine
# Location: engine/orchestration_engine.py
"""
Create the foundational graph-based workflow engine using LangGraph.
Required components:
- Graph state manager with serialization/deserialization
- Node execution with error handling and retry logic
- Edge condition evaluation for dynamic routing
- Parallel execution support for concurrent subgraphs
- Checkpoint/resume functionality for long-running tasks
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional, Sequence

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import CONFIG_KEY_NODE_FINISHED
from opentelemetry import trace

from engine.state import State

GraphState = State

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class Node:
    """Representation of a node in the workflow graph."""

    name: str
    func: (Callable[[State], Awaitable[State]] | Callable[[State], State])
    retries: int = 0

    async def run(self, state: State) -> State:
        for attempt in range(self.retries + 1):
            try:
                with tracer.start_as_current_span(f"node:{self.name}"):
                    if asyncio.iscoroutinefunction(self.func):
                        result = await self.func(state)
                    else:
                        result = self.func(state)
                if isinstance(result, GraphState):
                    return result
                if isinstance(result, dict):
                    state.update(result)
                    return state
                raise ValueError("Node returned unsupported type")
            except Exception as exc:  # pragma: no cover - logging path
                logger.exception("Node %s failed on attempt %s", self.name, attempt + 1)
                if attempt >= self.retries:
                    raise exc
                await asyncio.sleep(2**attempt)
        return state


async def parallel_subgraphs(
    subgraphs: Sequence["OrchestrationEngine"], state: State
) -> State:
    """Execute multiple subgraphs concurrently and merge their state."""

    results = await asyncio.gather(*(sg.run_async(state) for sg in subgraphs))
    merged = State(
        data=state.data.copy(), messages=list(state.messages), status=state.status
    )
    for res in results:
        merged.update(res.data)
    return merged


def _build_order(edges: Iterable[tuple[str, str]]) -> Dict[str, str]:
    """Convert edge list to lookup map."""

    return {start: end for start, end in edges}


@dataclass
class OrchestrationEngine:
    """Core LangGraph-based orchestration engine."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    routers: list[
        tuple[str, Callable[[State], str | Iterable[str]], Dict[str, str] | None]
    ] = field(default_factory=list)
    checkpointer: InMemorySaver = field(default_factory=InMemorySaver)
    _graph: Optional[Any] = field(init=False, default=None)
    _last_node: Optional[str] = field(init=False, default=None)

    def add_node(
        self,
        name: str,
        func: (Callable[[State], Awaitable[State]] | Callable[[State], State]),
        *,
        retries: int = 0,
    ) -> None:
        self.nodes[name] = Node(name, func, retries)

    def add_edge(self, start: str, end: str) -> None:
        self.edges.append((start, end))

    def add_router(
        self,
        start: str,
        router: Callable[[State], str | Iterable[str]],
        path_map: Dict[str, str] | None = None,
    ) -> None:
        self.routers.append((start, router, path_map))

    def _on_node_finished(self, name: str) -> None:
        if self._last_node is not None and self._last_node != name:
            with tracer.start_as_current_span(
                "edge", attributes={"from": self._last_node, "to": name}
            ):
                pass
        self._last_node = name

    def build(self) -> None:
        self.entry = next(iter(self.nodes)) if self.nodes else None
        self.order = _build_order(self.edges)
        self.finish = list(self.nodes)[-1] if self.nodes else None
        self.routers_map = {
            start: (router, path_map) for start, router, path_map in self.routers
        }

    async def run_async(self, state: State, *, thread_id: str = "default") -> State:
        if self.entry is None:
            self.build()
        self._last_node = None
        config = {
            "configurable": {
                "thread_id": thread_id,
                CONFIG_KEY_NODE_FINISHED: self._on_node_finished,
            }
        }
        result = await self._graph.ainvoke(state, config)
        return GraphState.model_validate(result)

    def run(self, state: GraphState, *, thread_id: str = "default") -> GraphState:
        if self._graph is None:
            self.build()
        self._last_node = None
        config = {
            "configurable": {
                "thread_id": thread_id,
                CONFIG_KEY_NODE_FINISHED: self._on_node_finished,
            }
        }
        result = self._graph.invoke(state, config)
        return GraphState.model_validate(result)

    def export_dot(self) -> str:
        lines = ["digraph Orchestration {"]
        for name in self.nodes:
            lines.append(f'  "{name}";')
        for start, end in self.edges:
            lines.append(f'  "{start}" -> "{end}";')
        for start, _, path_map in self.routers:
            if path_map:
                for label, dest in path_map.items():
                    lines.append(f'  "{start}" -> "{dest}" [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)


def create_orchestration_engine() -> OrchestrationEngine:
    """Factory function for the core orchestration engine."""

    return OrchestrationEngine()
