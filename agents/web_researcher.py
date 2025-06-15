"""WebResearcher Agent implementation."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
from engine.state import State
from engine.orchestration_engine import GraphState
from services.tracing.tracing_schema import ToolCallTrace


class WebResearcherAgent:
    def __init__(
        self,
        tool_registry: Dict[str, Callable[..., Any]],
        *,
        rate_limit_per_minute: int = 5,
    ) -> None:
        """Initialize with secure tool access and rate limiting."""
        self.tool_registry = tool_registry
        self.rate_limit = rate_limit_per_minute
        self.call_times: List[float] = []

        # Required tools
        self.web_search = self._require_tool("web_search")
        self.pdf_extract = self.tool_registry.get("pdf_extract")
        self.html_scraper = self.tool_registry.get("html_scraper")
        self.summarize = self._require_tool("summarize")
        self.assess_source = self.tool_registry.get("assess_source", lambda url: 1.0)

    def _summarize_for_task(self, text: str, task: str) -> str:
        """Summarize ``text`` with focus on the current sub-task."""
        prompt = f"Summarize the following text focusing only on information relevant to '{task}':\n{text}"
        return self.summarize(prompt)

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

    def research_topic(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive web research on specified topic."""
        self._check_rate_limit()
        start = time.perf_counter()
        search_results = self.web_search(topic)
        latency_ms = (time.perf_counter() - start) * 1000
        ToolCallTrace(
            agent_id=str(context.get("agent_id", "")),
            agent_role="WebResearcher",
            tool_name="web_search",
            tool_input=topic,
            tool_output=search_results,
            latency_ms=latency_ms,
        ).record()
        processed: List[Dict[str, Any]] = []
        for r in search_results:
            url = r.get("url")
            if not url:
                continue
            credibility = float(self.assess_source(url))
            if credibility < 0.5:
                continue

            content: Optional[str] = None
            if url.lower().endswith(".pdf") and self.pdf_extract:
                content = self.pdf_extract(url)
            elif self.html_scraper:
                content = self.html_scraper(url)
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
    def __call__(self, state: "GraphState") -> "GraphState":
        """Graph node entrypoint for orchestrated execution."""
        task: str | None = state.data.get("sub_task")
        if not task:
            return state

        # Simple query crafting with light "interleaved thinking": strip verbs
        query = task.lower().replace("find papers on", "").strip()
        if query and "academic papers" not in query:
            query = f"{query} academic papers"

        result = self.research_topic(query, {"agent_id": state.data.get("agent_id")})
        state.update({"research_result": result})
        return state
