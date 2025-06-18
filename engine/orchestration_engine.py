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
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional, Sequence

try:  # optional dependency
    from opentelemetry import trace
except Exception:  # pragma: no cover - fallback tracer
    import contextlib

    class _Tracer:
        def start_as_current_span(self, *_a, **_k):
            return contextlib.nullcontext()

    class _Trace:
        def get_tracer(self, *_a, **_k):
            return _Tracer()

    trace = _Trace()

from services.tracing import get_metrics, reset_metrics

from .state import State

CONFIG_KEY_NODE_FINISHED = "callbacks.on_node_finished"

# ``GraphState`` is currently an alias of ``State``. Future iterations may
# introduce a dedicated class with additional orchestration-specific fields.

GraphState = State

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Enumeration of built-in node types."""

    DEFAULT = "default"
    HUMAN_IN_THE_LOOP_BREAKPOINT = "human_in_the_loop_breakpoint"
    GROUP_CHAT_MANAGER = "group_chat_manager"
    SUBGRAPH = "subgraph"
    PRIVILEGED = "privileged"
    QUARANTINED = "quarantined"


class InMemorySaver:
    """Minimal in-memory checkpoint stub used for testing."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, State]] = {}

    def save(
        self, run_id: str, node: str, state: State
    ) -> None:  # pragma: no cover - util
        self._data[run_id] = (node, state)

    def load(self, run_id: str) -> tuple[str, State] | None:  # pragma: no cover - util
        return self._data.get(run_id)


def _merge_states(parent: State, child: State) -> State:
    """Merge child state into parent state and return the updated parent."""

    parent.update(child.data)
    parent.messages.extend(child.messages)
    parent.history.extend(child.history)
    parent.scratchpad.update(child.scratchpad)
    parent.status = child.status
    parent.evaluator_feedback = child.evaluator_feedback
    parent.retry_count = child.retry_count
    return parent


@dataclass
class Node:
    """Representation of a node in the workflow graph."""

    name: str
    func: (
        Callable[[State, Dict[str, Any]], Awaitable[State]]
        | Callable[[State, Dict[str, Any]], State]
    )

    retries: int = 0
    node_type: NodeType = NodeType.DEFAULT

    async def run(self, state: State) -> State:
        if (
            self.node_type == NodeType.PRIVILEGED
            and state.data.get("risk_level") == "high"
        ):
            raise PermissionError("privileged agent cannot process high-risk input")
        for attempt in range(self.retries + 1):
            try:
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(
                    f"node:{self.name}",
                    attributes={"state_in": state.model_dump_json()},
                ) as span:
                    if self.node_type == NodeType.SUBGRAPH:
                        if isinstance(self.func, OrchestrationEngine):
                            result = await self.func.run_async(state)
                            if isinstance(result, GraphState):
                                state.scratchpad.update(result.scratchpad)
                        else:
                            raise TypeError(
                                "subgraph node must be an OrchestrationEngine"
                            )
                    elif asyncio.iscoroutinefunction(self.func):
                        result = await self.func(state, state.scratchpad)
                    else:
                        result = self.func(state, state.scratchpad)

                    if isinstance(result, GraphState):
                        if self.node_type == NodeType.SUBGRAPH:
                            out_state = _merge_states(state, result)
                        else:
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


@dataclass
class Edge:
    """Connection between two nodes."""

    start: str
    end: str
    edge_type: str | None = None


async def parallel_subgraphs(
    subgraphs: Sequence["OrchestrationEngine"], state: State
) -> State:
    """Execute multiple subgraphs concurrently and merge their state."""

    results = await asyncio.gather(*(sg.run_async(state) for sg in subgraphs))
    merged = State(
        data=state.data.copy(),
        messages=list(state.messages),
        history=list(state.history),
        scratchpad=state.scratchpad.copy(),
        status=state.status,
    )
    for res in results:
        merged.update(res.data)
        merged.messages.extend(res.messages)
        merged.history.extend(res.history)
    return merged


def _build_order(
    edges: Iterable[Edge | tuple[str, str, str | None] | tuple[str, str]],
) -> Dict[str, str]:
    """Convert edge list to lookup map."""

    order: Dict[str, str] = {}
    for edge in edges:
        if isinstance(edge, Edge):
            order[edge.start] = edge.end
        else:
            start, end = edge[:2]
            order[start] = end
    return order


@dataclass
class OrchestrationEngine:
    """Core LangGraph-based orchestration engine."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    routers: list[
        tuple[str, Callable[[State], str | Iterable[str]], Dict[str, str] | None]
    ] = field(default_factory=list)

    # Using ``Any`` here avoids importing optional dependencies for the dummy
    # checkpointer implementation used in tests.
    checkpointer: Any = field(default_factory=dict)
    review_queue: Any | None = None
    quarantine_node: str | None = None
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
        func: Callable[[State], Awaitable[State]] | Callable[[State], State],
        *,
        retries: int = 0,
        node_type: NodeType = NodeType.DEFAULT,
    ) -> None:
        self.nodes[name] = Node(name, func, retries, node_type)

    def add_subgraph(
        self, name: str, subgraph: "OrchestrationEngine", *, retries: int = 0
    ) -> None:
        """Add a subgraph node that runs another :class:`OrchestrationEngine`."""
        self.nodes[name] = Node(name, subgraph, retries, NodeType.SUBGRAPH)

    def add_edge(self, start: str, end: str, *, edge_type: str | None = None) -> None:
        self.edges.append(Edge(start=start, end=end, edge_type=edge_type))

    def add_router(
        self,
        start: str,
        router: Callable[[State], str | Iterable[str]],
        path_map: Dict[str, str] | None = None,
    ) -> None:
        self.routers.append((start, router, path_map))

    def set_quarantine_node(self, name: str) -> None:
        """Designate the node used for quarantined execution."""
        self.quarantine_node = name

    def _should_quarantine(self, node: Node, state: State) -> bool:
        """Return ``True`` if the node should be redirected to the quarantine path."""
        return (
            node.node_type == NodeType.PRIVILEGED
            and state.data.get("risk_level") == "high"
            and self.quarantine_node is not None
        )

    def _on_node_finished(self, name: str) -> None:
        if self._last_node is not None and self._last_node != name:
            tracer = trace.get_tracer(__name__)
            edge_type = None
            for edge in self.edges:
                if edge.start == self._last_node and edge.end == name:
                    edge_type = edge.edge_type
                    break
            with tracer.start_as_current_span(
                "edge",
                attributes={"from": self._last_node, "to": name, "type": edge_type},
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

    async def run_async(
        self, state: State, *, thread_id: str = "default", start_at: str | None = None
    ) -> State:
        """Execute the graph asynchronously in a simple sequential manner."""

        tracer = trace.get_tracer(__name__)
        start_time = time.perf_counter()
        reset_metrics()
        with tracer.start_as_current_span(
            "task", attributes={"thread_id": thread_id}
        ) as task_span:
            if self.entry is None:
                self.build()
            self._last_node = None
            if hasattr(self.checkpointer, "start"):
                try:
                    self.checkpointer.start(thread_id, state)
                except Exception:  # pragma: no cover - defensive
                    pass

            node_name = start_at or self.entry
            while node_name:
                node = self.nodes[node_name]
                if self._should_quarantine(node, state):
                    node_name = self.quarantine_node
                    continue
                prev_state = state
                next_state = await node.run(state)
                if node.node_type == NodeType.SUBGRAPH and isinstance(
                    next_state, GraphState
                ):
                    state = _merge_states(prev_state, next_state)
                else:
                    state = next_state
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
                next_node = dest if isinstance(dest, str) else None
            else:
                next_node = self.order.get(node_name)

            if node.node_type == NodeType.HUMAN_IN_THE_LOOP_BREAKPOINT:
                state.update({"status": "PAUSED"})
                if hasattr(self.review_queue, "enqueue"):
                    self.review_queue.enqueue(thread_id, state, next_node)
                return state

            node_name = next_node
        if self.on_complete:
            try:
                if asyncio.iscoroutinefunction(self.on_complete):
                    state = await self.on_complete(state)
                else:
                    state = self.on_complete(state)
            except Exception:  # pragma: no cover - defensive
                logger.exception("on_complete hook failed")

        duration = time.perf_counter() - start_time
        conv = state.data.get("conversation", [])
        total_messages = len(conv) if isinstance(conv, list) else 0
        communication_tokens = (
            sum(len(str(m.get("content", "")).split()) for m in conv)
            if isinstance(conv, list)
            else 0
        )
        latencies = [
            conv[i + 1]["timestamp"] - conv[i]["timestamp"]
            for i in range(len(conv) - 1)
            if isinstance(conv[i], dict)
            and isinstance(conv[i + 1], dict)
            and "timestamp" in conv[i]
            and "timestamp" in conv[i + 1]
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        action_rate = (len(state.history) / duration) if duration > 0 else 0.0
        metrics = get_metrics()
        tokens = metrics.get("total_tokens_consumed", 0.0)
        tool_calls = metrics.get("tool_call_count", 0.0)
        self_corrections = float(state.retry_count)

        task_span.set_attribute("total_messages_sent", total_messages)
        task_span.set_attribute("average_message_latency", avg_latency)
        task_span.set_attribute("action_advancement_rate", action_rate)
        task_span.set_attribute("total_tokens_consumed", tokens)
        task_span.set_attribute("tool_call_count", tool_calls)
        task_span.set_attribute("self_correction_loops", self_corrections)
        task_span.set_attribute("communication_overhead", communication_tokens)

        return state

    def run(self, state: GraphState, *, thread_id: str = "default") -> GraphState:
        """Synchronous wrapper around :meth:`run_async`."""
        return asyncio.run(self.run_async(state, thread_id=thread_id))

    async def resume_from_queue_async(self, run_id: str) -> State:
        if not self.review_queue:
            raise ValueError("No review queue configured")
        state, next_node = self.review_queue.pop(run_id)
        state.update({"status": None})
        return await self.run_async(state, thread_id=run_id, start_at=next_node)

    def resume_from_queue(self, run_id: str) -> State:
        return asyncio.run(self.resume_from_queue_async(run_id))

    # ------------------------------------------------------------------
    # Checkpointing helpers
    # ------------------------------------------------------------------

    def _determine_next_node(self, node: str, state: State) -> str | None:
        if node in self.routers_map:
            router, path_map = self.routers_map[node]
            dest = router(state)
            if path_map:
                dest = path_map.get(dest, dest)
            return dest if isinstance(dest, str) else None
        return self.order.get(node)

    async def resume_from_checkpoint_async(self, run_id: str) -> State:
        if not hasattr(self.checkpointer, "load"):
            raise ValueError("No checkpointer configured")
        loaded = self.checkpointer.load(run_id)
        if not loaded:
            raise ValueError(f"No checkpoint found for {run_id}")
        node, state = loaded
        if self.entry is None:
            self.build()
        next_node = self._determine_next_node(node, state)
        return await self.run_async(state, thread_id=run_id, start_at=next_node)

    def resume_from_checkpoint(self, run_id: str) -> State:
        return asyncio.run(self.resume_from_checkpoint_async(run_id))

    def get_edges(
        self, start: str | None = None, edge_type: str | None = None
    ) -> list[Edge]:
        """Return edges matching the optional criteria."""

        matches: list[Edge] = []
        for edge in self.edges:
            if start is not None and edge.start != start:
                continue
            if edge_type is not None and edge.edge_type != edge_type:
                continue
            matches.append(edge)
        return matches

    def export_dot(self) -> str:
        lines = ["digraph Orchestration {"]
        for name in self.nodes:
            lines.append(f'  "{name}";')
        for edge in self.edges:
            label = f' [label="{edge.edge_type}"]' if edge.edge_type else ""
            lines.append(f'  "{edge.start}" -> "{edge.end}"{label};')
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
