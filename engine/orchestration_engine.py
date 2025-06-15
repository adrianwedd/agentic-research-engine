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
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GraphState(BaseModel):
    """Simple container for data exchanged between graph nodes."""

    data: Dict[str, Any] = Field(default_factory=dict)

    def update(self, other: Dict[str, Any]) -> None:
        self.data.update(other)

    def to_json(self) -> str:  # pragma: no cover - thin wrapper
        return self.model_dump_json()

    @classmethod
    def from_json(cls, payload: str) -> "GraphState":  # pragma: no cover - thin wrapper
        return cls.model_validate_json(payload)


@dataclass
class Node:
    """Representation of a node in the workflow graph."""

    name: str
    func: (
        Callable[[GraphState], Awaitable[GraphState]]
        | Callable[[GraphState], GraphState]
    )
    retries: int = 0

    async def run(self, state: GraphState) -> GraphState:
        for attempt in range(self.retries + 1):
            try:
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
    subgraphs: Sequence["OrchestrationEngine"], state: GraphState
) -> GraphState:
    """Execute multiple subgraphs concurrently and merge their state."""

    results = await asyncio.gather(*(sg.run_async(state) for sg in subgraphs))
    merged = GraphState(data=state.data.copy())
    for res in results:
        merged.update(res.data)
    return merged


def _build_graph(
    nodes: Iterable[Node],
    edges: Iterable[tuple[str, str]] | None = None,
    routers: (
        Iterable[
            tuple[
                str, Callable[[GraphState], str | Iterable[str]], Dict[str, str] | None
            ]
        ]
        | None
    ) = None,
    entrypoint: str | None = None,
    finish: str | None = None,
) -> StateGraph:
    builder = StateGraph(GraphState)
    for node in nodes:
        builder.add_node(node.name, node.run)
    if edges:
        for start, end in edges:
            builder.add_edge(start, end)
    if routers:
        for start, router, path_map in routers:
            builder.add_conditional_edges(start, router, path_map)
    if entrypoint:
        builder.set_entry_point(entrypoint)
    if finish:
        builder.set_finish_point(finish)
    return builder


@dataclass
class OrchestrationEngine:
    """Core LangGraph-based orchestration engine."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    routers: list[
        tuple[str, Callable[[GraphState], str | Iterable[str]], Dict[str, str] | None]
    ] = field(default_factory=list)
    checkpointer: InMemorySaver = field(default_factory=InMemorySaver)
    _graph: Optional[Any] = field(init=False, default=None)

    def add_node(
        self,
        name: str,
        func: (
            Callable[[GraphState], Awaitable[GraphState]]
            | Callable[[GraphState], GraphState]
        ),
        *,
        retries: int = 0,
    ) -> None:
        self.nodes[name] = Node(name, func, retries)

    def add_edge(self, start: str, end: str) -> None:
        self.edges.append((start, end))

    def add_router(
        self,
        start: str,
        router: Callable[[GraphState], str | Iterable[str]],
        path_map: Dict[str, str] | None = None,
    ) -> None:
        self.routers.append((start, router, path_map))

    def build(self) -> None:
        entry = next(iter(self.nodes)) if self.nodes else None
        finish = list(self.nodes)[-1] if self.nodes else None
        builder = _build_graph(
            self.nodes.values(), self.edges, self.routers, entry, finish
        )
        self._graph = builder.compile(checkpointer=self.checkpointer)

    async def run_async(
        self, state: GraphState, *, thread_id: str = "default"
    ) -> GraphState:
        if self._graph is None:
            self.build()
        config = {"configurable": {"thread_id": thread_id}}
        return await self._graph.ainvoke(state, config)

    def run(self, state: GraphState, *, thread_id: str = "default") -> GraphState:
        if self._graph is None:
            self.build()
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(state, config)


def create_orchestration_engine() -> OrchestrationEngine:
    """Factory function for the core orchestration engine."""

    return OrchestrationEngine()
