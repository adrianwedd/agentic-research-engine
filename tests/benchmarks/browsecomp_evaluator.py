"""BrowseComp benchmark evaluation utilities."""

from __future__ import annotations

import datetime
import json
import time
from typing import Any, Dict, Iterable


class BrowseCompEvaluator:
    """Execute BrowseComp-style benchmark suites."""

    def __init__(self, test_cases_path: str) -> None:
        """Load standardized benchmark test cases."""
        with open(test_cases_path, "r", encoding="utf-8") as f:
            self.test_cases: Iterable[Dict[str, Any]] = json.load(f)
        self.history: list[Dict[str, Any]] = []

    def _call_agent(self, agent_system: Any, question: str) -> Any:
        if callable(agent_system):
            return agent_system(question)
        if hasattr(agent_system, "run") and callable(agent_system.run):
            return agent_system.run(question)
        raise TypeError("agent_system must be callable or have a 'run' method")

    def run_benchmark_suite(self, agent_system: Any) -> Dict[str, Any]:
        """Run the benchmark and return aggregated metrics."""
        results = []
        for case in self.test_cases:
            question = case.get("question", "")
            expected = case.get("answer", "").strip().lower()
            start = time.monotonic()
            try:
                response = self._call_agent(agent_system, question)
            except Exception as e:  # pragma: no cover - safety guard
                end = time.monotonic()
                results.append(
                    {
                        "question": question,
                        "error": str(e),
                        "response_time": end - start,
                        "success": False,
                    }
                )
                continue
            end = time.monotonic()
            answer = (
                response.get("answer") if isinstance(response, dict) else str(response)
            )
            success = expected in answer.strip().lower()
            results.append(
                {
                    "question": question,
                    "expected": expected,
                    "answer": answer,
                    "success": success,
                    "response_time": end - start,
                }
            )
        passed = sum(1 for r in results if r.get("success"))
        summary = {
            "total_cases": len(results),
            "passed": passed,
            "pass_rate": passed / len(results) if results else 0.0,
            "results": results,
        }
        self.history.append(
            {"timestamp": datetime.datetime.now(datetime.UTC).isoformat(), **summary}
        )
        return summary
