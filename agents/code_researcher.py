from __future__ import annotations

"""CodeResearcher Agent implementation."""

import time
from typing import Any, Callable, Dict, List, Optional

from engine.orchestration_engine import GraphState
from services.tool_registry import ToolRegistry

from .base import BaseAgent


class CodeResearcherAgent(BaseAgent):
    """Agent specializing in code analysis and execution."""

    def __init__(
        self,
        tool_registry: Dict[str, Callable[..., Any]] | ToolRegistry,
        *,
        rate_limit_per_minute: int = 5,
        max_retries: int = 3,
        ltm_endpoint: str | None = None,
    ) -> None:
        super().__init__("CodeResearcher", tool_registry, ltm_endpoint=ltm_endpoint)
        self.tool_registry = tool_registry  # type: ignore[assignment]
        self.rate_limit = rate_limit_per_minute
        self.max_retries = max_retries
        self.call_times: List[float] = []

        self.code_interpreter = self._require_tool("code_interpreter")

    def _require_tool(self, name: str) -> Callable[..., Any]:
        tool = self.tool_registry.get(name)
        if not callable(tool):
            raise ValueError(f"Required tool '{name}' not available")
        return tool

    def _check_rate_limit(self) -> None:
        now = time.time()
        self.call_times = [t for t in self.call_times if now - t < 60]
        if len(self.call_times) >= self.rate_limit:
            raise RuntimeError("Rate limit exceeded")
        self.call_times.append(now)

    def _call_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        tool_name: str | None = None,
        trace_kwargs: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        backoff = 1.0
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                if tool_name:
                    self._log_tool(
                        tool_name, list(args), kwargs, result, **(trace_kwargs or {})
                    )
                return result
            except Exception as exc:
                if attempt >= self.max_retries - 1:
                    raise RuntimeError(
                        f"{func.__name__} failed after {self.max_retries} attempts: {exc}"
                    ) from exc
                time.sleep(backoff)
                backoff *= 2

    def analyze_code(
        self, code: str, args: Optional[List[str]] | None = None
    ) -> Dict[str, Any]:
        """Execute ``code`` via the code interpreter with optional ``args``."""
        self._check_rate_limit()
        start = time.perf_counter()
        try:
            result = self._call_with_retry(
                self.code_interpreter,
                code,
                args=args or [],
            )
        except Exception as exc:
            result = {"stdout": "", "stderr": str(exc), "returncode": -1}
        latency_ms = (time.perf_counter() - start) * 1000
        self._log_tool(
            "code_interpreter",
            [code],
            {"args": args or []},
            result,
            latency_ms=latency_ms,
        )
        return result

    # ------------------------------------------------------------------
    # Graph node integration
    # ------------------------------------------------------------------
    def __call__(self, state: "GraphState", scratchpad: Dict[str, Any]) -> "GraphState":
        if self._execute_stored_procedure(state):
            self._store_procedure(state)
            return state

        code = state.data.get("code")
        if not code:
            return state
        args = state.data.get("code_args", [])
        result = self.analyze_code(code, args)
        state.update({"code_result": result})
        self._store_procedure(state)
        return state
