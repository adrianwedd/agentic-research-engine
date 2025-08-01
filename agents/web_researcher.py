"""WebResearcher Agent implementation."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Callable, Dict, List, Optional

from engine.orchestration_engine import GraphState
from engine.state import State
from services.tool_registry import ToolRegistry, ToolRegistryAsyncClient

from .base import BaseAgent


class WebResearcherAgent(BaseAgent):
    def __init__(
        self,
        tool_registry: Dict[str, Callable[..., Any]] | ToolRegistry,
        *,
        rate_limit_per_minute: int = 5,
        max_retries: int = 2,
        ltm_endpoint: str | None = None,
    ) -> None:
        """Initialize with secure tool access and rate limiting."""
        super().__init__("WebResearcher", tool_registry, ltm_endpoint=ltm_endpoint)
        if not isinstance(tool_registry, (ToolRegistry, ToolRegistryAsyncClient)):
            self.tool_registry = tool_registry  # type: ignore[assignment]
        self.rate_limit = rate_limit_per_minute
        self.max_retries = max_retries
        self.call_times: List[float] = []

        # ensure required tools exist
        self._require_tool("web_search")
        self._require_tool("summarize")

    def _summarize_for_task(self, text: str | None, task: str) -> str:
        """Summarize ``text`` with focus on the current sub-task."""
        if not isinstance(text, str) or not text.strip():
            return ""

        prompt = (
            "Summarize the following text focusing only on information "
            f"relevant to '{task}'. Limit the summary to 200 words or fewer:\n{text}"
        )
        summary = self._call_with_retry(
            self._invoke_tool,
            "summarize",
            prompt,
            tool_name="summarize",
            trace_kwargs={"agent_id": "", "tool_input": prompt},
        )
        if isinstance(summary, str) and len(summary.split()) > 200:
            summary = " ".join(summary.split()[:200])
        return summary

    def summarize_to_state(
        self, state: State, *, text_key: str = "raw_text", task_key: str = "task"
    ) -> State:
        """Condense ``state.data[text_key]`` and append the summary to messages."""
        raw_text = state.data.get(text_key)
        if not raw_text:
            return state
        task = state.data.get(task_key, "")
        summary = self._summarize_for_task(raw_text, task)
        state.add_message({"role": "WebResearcher", "content": summary})
        return state

    def _require_tool(self, name: str) -> str:
        if self.registry is not None:
            self.registry.get_tool(self.role, name)
        else:
            tool = self.tool_registry.get(name)
            if not callable(tool):
                raise ValueError(f"Required tool '{name}' not available")
        return name

    def _invoke_tool(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if self.registry is not None:
            return self.registry.invoke(self.role, name, *args, **kwargs)
        if hasattr(self, "async_registry") and self.async_registry is not None:
            return asyncio.run(
                self.async_registry.invoke(self.role, name, *args, **kwargs)
            )
        tool = self.tool_registry[name]
        return tool(*args, **kwargs)

    def _has_tool(self, name: str) -> bool:
        if self.registry is not None:
            try:
                self.registry.get_tool(self.role, name)
                return True
            except Exception:
                return False
        if hasattr(self, "async_registry") and self.async_registry is not None:
            try:
                asyncio.run(self.async_registry.get_tool(self.role, name))
                return True
            except Exception:
                return False
        return callable(self.tool_registry.get(name)) if self.tool_registry else False

    def _check_rate_limit(self) -> None:
        if os.getenv("PYTEST_DISABLE_RATE_LIMIT"):
            return
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
        """Call ``func`` with simple exponential backoff retries."""
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

    def research_topic(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive web research on specified topic."""
        self._check_rate_limit()
        if self._has_tool("knowledge_graph_search"):
            try:
                facts = self._call_with_retry(
                    self._invoke_tool,
                    "knowledge_graph_search",
                    {"text": topic},
                    tool_name="knowledge_graph_search",
                    trace_kwargs={
                        "agent_id": context.get("agent_id", ""),
                        "tool_input": {"text": topic},
                    },
                )
            except Exception:
                facts = []
            if facts:
                return {
                    "topic": topic,
                    "facts": facts,
                    "sources": [],
                    "confidence": 1.0,
                }

        start = time.perf_counter()
        search_results = self._call_with_retry(
            self._invoke_tool,
            "web_search",
            topic,
            tool_name="web_search",
        )
        latency_ms = (time.perf_counter() - start) * 1000
        self._log_tool(
            "web_search",
            [topic],
            {},
            search_results,
            agent_id=str(context.get("agent_id", "")),
            input_tokens=len(str(topic).split()),
            output_tokens=len(str(search_results).split()),
            latency_ms=latency_ms,
        )
        processed: List[Dict[str, Any]] = []
        for r in search_results:
            url = r.get("url")
            if not url:
                continue
            if self._has_tool("assess_source"):
                credibility = float(self._invoke_tool("assess_source", url))
            else:
                credibility = 1.0
            if credibility < 0.5:
                continue

            content: Optional[str] = None
            if url.lower().endswith(".pdf") and self._has_tool("pdf_extract"):
                content = self._call_with_retry(
                    self._invoke_tool,
                    "pdf_extract",
                    url,
                    tool_name="pdf_extract",
                    trace_kwargs={
                        "agent_id": str(context.get("agent_id", "")),
                        "tool_input": url,
                    },
                )
            elif self._has_tool("html_scraper"):
                content = self._call_with_retry(
                    self._invoke_tool,
                    "html_scraper",
                    url,
                    tool_name="html_scraper",
                    trace_kwargs={
                        "agent_id": str(context.get("agent_id", "")),
                        "tool_input": url,
                    },
                )
            if not content:
                continue

            summary = self._summarize_for_task(content, topic)
            processed.append(
                {
                    "url": url,
                    "title": r.get("title", ""),
                    "summary": summary,
                    "credibility": credibility,
                }
            )

        confidence = (
            sum(p["credibility"] for p in processed) / len(processed)
            if processed
            else 0.0
        )
        return {"topic": topic, "sources": processed, "confidence": confidence}

    # ------------------------------------------------------------------
    # Graph node integration
    # ------------------------------------------------------------------
    def __call__(self, state: "GraphState", scratchpad: Dict[str, Any]) -> "GraphState":
        """Graph node entrypoint for orchestrated execution.

        Parameters
        ----------
        state:
            The orchestration state.
        scratchpad:
            Shared scratchpad (unused by default).
        """
        if self._execute_stored_procedure(state):
            self._store_procedure(state)
            return state

        task: str | None = state.data.get("sub_task")
        if not task:
            return state

        # Simple query crafting with light "interleaved thinking": strip verbs
        query = task.lower().replace("find papers on", "").strip()
        if query and "academic papers" not in query:
            query = f"{query} academic papers"

        result = self.research_topic(query, {"agent_id": state.data.get("agent_id")})
        state.update({"research_result": result})
        self._store_procedure(state)
        return state
