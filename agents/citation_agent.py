from __future__ import annotations

"""CitationAgent for source-claim matching and citation formatting."""

import difflib
import re
from typing import Any, Dict, List, Optional

from engine.orchestration_engine import GraphState

from .base import BaseAgent


class CitationAgent(BaseAgent):
    """Match report claims to sources and insert formatted citations."""

    def __init__(
        self,
        tool_registry: Optional[Dict[str, Any]] = None,
        *,
        default_style: str = "APA",
    ) -> None:
        super().__init__("CitationAgent", tool_registry)
        self.default_style = default_style

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------
    def _split_sentences(self, text: str) -> List[str]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        return sentences

    def _match_source(
        self, claim: str, sources: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Return the source with highest similarity to ``claim``."""
        best: Optional[Dict[str, Any]] = None
        best_score = 0.0
        for src in sources:
            text = str(src.get("text", ""))
            ratio = difflib.SequenceMatcher(None, claim.lower(), text.lower()).ratio()
            if ratio > best_score:
                best_score = ratio
                best = src
        return best

    def _format_citation(self, source: Dict[str, Any], style: str) -> str:
        author = source.get("author", "Unknown")
        title = source.get("title", "Untitled")
        year = source.get("year", "n.d.")
        url = source.get("url", "")
        if style.lower() == "mla":
            return f'{author}. "{title}." {year}. {url}'.strip()
        return f"{author} ({year}). {title}. {url}".strip()

    def cite_report(
        self, report: str, sources: List[Dict[str, Any]], *, style: str | None = None
    ) -> Dict[str, Any]:
        style = style or self.default_style
        sentences = self._split_sentences(report)
        citations: List[str] = []
        processed: List[str] = []
        for sent in sentences:
            src = self._match_source(sent, sources)
            if src:
                cite = self._format_citation(src, style)
                citations.append(cite)
                sent = f"{sent} ({cite})"
            processed.append(sent)
        return {"report": " ".join(processed), "citations": citations}

    # ------------------------------------------------------------------
    # Graph node integration
    # ------------------------------------------------------------------
    def __call__(self, state: GraphState, scratchpad: Dict[str, Any]) -> GraphState:
        report = state.data.get("report")
        sources = state.data.get("sources")
        if not isinstance(report, str) or not isinstance(sources, list):
            return state
        style = state.data.get("citation_style", self.default_style)
        result = self.cite_report(report, sources, style=style)
        state.update(result)
        return state
