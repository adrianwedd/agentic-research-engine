from __future__ import annotations

"""Base agent class with skill logging support."""

import asyncio
from typing import Any, Dict, List, Optional

from engine.state import State
from services.tool_registry import (
    ToolRegistry,
    ToolRegistryAsyncClient,
    create_default_registry,
)
from services.tracing.tracing_schema import ToolCallTrace


class BaseAgent:
    """Base class providing tool call tracing and procedure storage."""

    def __init__(
        self,
        role: str,
        tool_registry: ToolRegistry | Dict[str, Any] | None = None,
        *,
        ltm_endpoint: str | None = None,
    ) -> None:
        self.role = role
        if isinstance(tool_registry, ToolRegistry):
            self.registry: Optional[ToolRegistry] = tool_registry
            self.async_registry: Optional[ToolRegistryAsyncClient] = None
            self.tool_registry = tool_registry
        elif isinstance(tool_registry, ToolRegistryAsyncClient):
            self.registry = None
            self.async_registry = tool_registry
            self.tool_registry = None
        else:
            self.registry = None
            self.async_registry = None
            self.tool_registry = tool_registry or create_default_registry()
        self.ltm_endpoint = ltm_endpoint
        self._procedure: List[Dict[str, Any]] = []

    def _log_tool(
        self,
        name: str,
        args: List[Any],
        kwargs: Dict[str, Any],
        result: Any,
        *,
        agent_id: str = "",
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Record a tool invocation in the procedure and emit a trace span."""
        self._procedure.append({"action": name, "args": args, "kwargs": kwargs})
        ToolCallTrace(
            agent_id=agent_id,
            agent_role=self.role,
            tool_name=name,
            tool_input={"args": args, "kwargs": kwargs},
            tool_output=result,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        ).record()

    def _store_procedure(self, state: State) -> None:
        """Persist the recorded procedure to procedural memory."""
        if not self._procedure or (
            self.registry is None and self.async_registry is None
        ):
            return
        state.history.append({"action": "procedure", "steps": self._procedure})
        try:
            if self.registry is not None:
                self.registry.invoke(
                    self.role,
                    "consolidate_memory",
                    {
                        "task_context": state.data,
                        "procedure": self._procedure,
                        "outcome": {"success": True},
                    },
                    memory_type="procedural",
                    endpoint=self.ltm_endpoint,
                )
            else:
                asyncio.run(
                    self.async_registry.invoke(
                        self.role,
                        "consolidate_memory",
                        {
                            "task_context": state.data,
                            "procedure": self._procedure,
                            "outcome": {"success": True},
                        },
                        memory_type="procedural",
                        endpoint=self.ltm_endpoint,
                    )
                )
        except Exception:
            pass
        self._procedure = []

    def _execute_stored_procedure(self, state: State) -> bool:
        """Retrieve and run a stored procedure if available."""
        if self.registry is None and self.async_registry is None:
            return False
        try:
            if self.registry is not None:
                matches = self.registry.invoke(
                    self.role,
                    "retrieve_memory",
                    {"query": state.data},
                    memory_type="procedural",
                    limit=1,
                    endpoint=self.ltm_endpoint,
                )
            else:
                matches = asyncio.run(
                    self.async_registry.invoke(
                        self.role,
                        "retrieve_memory",
                        {"query": state.data},
                        memory_type="procedural",
                        limit=1,
                        endpoint=self.ltm_endpoint,
                    )
                )
        except Exception:
            return False
        if not matches:
            return False
        steps = matches[0].get("execution_trace", {}).get("procedure", [])
        if not steps:
            return False
        results: List[Any] = []
        for step in steps:
            action = step.get("action")
            args = step.get("args", [])
            kwargs = step.get("kwargs", {})
            try:
                if self.registry is not None:
                    result = self.registry.invoke(self.role, action, *args, **kwargs)
                elif self.async_registry is not None:
                    result = asyncio.run(
                        self.async_registry.invoke(self.role, action, *args, **kwargs)
                    )
                else:
                    tool = self.tool_registry.get(action)
                    result = tool(*args, **kwargs)
            except Exception:
                return False
            self._log_tool(action, list(args), kwargs, result)
            results.append(result)
        state.update({"procedure_result": results})
        return True
