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

from opentelemetry import trace

from .state import State

CONFIG_KEY_NODE_FINISHED = "callbacks.on_node_finished"

# ``GraphState`` is currently an alias of ``State``. Future iterations may
# introduce a dedicated class with additional orchestration-specific fields.

GraphState = State

logger = logging.getLogger(__name__)


class InMemorySaver:
    """Minimal in-memory checkpoint stub used for testing."""

    def __init__(self) -> None:
        self._data: dict[str, State] = {}

    def save(self, run_id: str, state: State) -> None:  # pragma: no cover - util
        self._data[run_id] = state

    def load(self, run_id: str) -> State | None:  # pragma: no cover - util
        return self._data.get(run_id)


@dataclass
class Node:
    """Representation of a node in the workflow graph."""

    name: str
    func: (Callable[[State], Awaitable[State]] | Callable[[State], State])
    retries: int = 0

    async def run(self, state: State) -> State:
        for attempt in range(self.retries + 1):
            try:
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(
                    f"node:{self.name}",
                    attributes={"state_in": state.model_dump_json()},
                ) as span:
                    if asyncio.iscoroutinefunction(self.func):
                        result = await self.func(state)
                    else:
                        result = self.func(state)

                    if isinstance(result, GraphState):
                        out_state = result
                    elif isinstance(result, dict):
                        state.update(result)
                        out_state = state
                    else:
                        raise ValueError("Node returned unsupported type")

                    span.set_attribute("state_out", out_state.model_dump_json())
                    return out_state
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
        data=state.data.copy(),
        messages=list(state.messages),
        history=list(state.history),
        status=state.status,
    )
    for res in results:
        merged.update(res.data)
        merged.messages.extend(res.messages)
        merged.history.extend(res.history)
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

    # Using ``Any`` here avoids importing optional dependencies for the dummy
    # checkpointer implementation used in tests.
    checkpointer: Any = field(default_factory=dict)
    _graph: Optional[Any] = field(init=False, default=None)
    _last_node: Optional[str] = field(init=False, default=None)
    entry: Optional[str] = field(init=False, default=None)
    order: Dict[str, str] = field(init=False, default_factory=dict)
    finish: Optional[str] = field(init=False, default=None)
    routers_map: Dict[
        str, tuple[Callable[[State], str | Iterable[str]], Dict[str, str] | None]
    ] = field(init=False, default_factory=dict)
    on_complete: Callable[[State], Awaitable[State] | State] | None = None

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
            tracer = trace.get_tracer(__name__)
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
        """Execute the graph asynchronously in a simple sequential manner."""

        if self.entry is None:
            self.build()
        self._last_node = None
        if hasattr(self.checkpointer, "start"):
            try:
                self.checkpointer.start(thread_id, state)
            except Exception:  # pragma: no cover - defensive
                pass

        node_name = self.entry
        while node_name:
            node = self.nodes[node_name]
            state = await node.run(state)
            if hasattr(self.checkpointer, "save"):
                try:
                    self.checkpointer.save(thread_id, node_name, state)
                except Exception:  # pragma: no cover - defensive
                    pass
            self._on_node_finished(node_name)

            if node_name in self.routers_map:
                router, path_map = self.routers_map[node_name]
                dest = router(state)
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(
                    "route",
                    attributes={"node": node_name, "decision": str(dest)},
                ):
                    pass
                if path_map:
                    dest = path_map.get(dest, dest)
                node_name = dest if isinstance(dest, str) else None
            else:
                node_name = self.order.get(node_name)
        if self.on_complete:
            try:
                if asyncio.iscoroutinefunction(self.on_complete):
                    state = await self.on_complete(state)
                else:
                    state = self.on_complete(state)
            except Exception:  # pragma: no cover - defensive
                logger.exception("on_complete hook failed")
        return state

    def run(self, state: GraphState, *, thread_id: str = "default") -> GraphState:
        """Synchronous wrapper around :meth:`run_async`."""
        return asyncio.run(self.run_async(state, thread_id=thread_id))

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


def create_orchestration_engine(
    *, memory_manager: Callable[[State], Awaitable[State] | State] | None = None
) -> OrchestrationEngine:
    """Factory function for the core orchestration engine."""

    return OrchestrationEngine(on_complete=memory_manager)
