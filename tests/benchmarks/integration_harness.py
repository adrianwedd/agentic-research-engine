"""Integration test harness for BrowseComp benchmarks."""

from __future__ import annotations

import concurrent.futures
import json
import statistics
import time
from pathlib import Path
from typing import Any, Callable

from .browsecomp_evaluator import BrowseCompEvaluator


class IntegrationTestHarness:
    """Run the BrowseComp benchmark with per-question timeouts."""

    def __init__(self, dataset_path: str, *, timeout: float = 30.0) -> None:
        self.evaluator = BrowseCompEvaluator(dataset_path)
        self.timeout = timeout

    def _execute_with_timeout(self, func: Callable[..., Any], *args: Any) -> Any:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(func, *args)
            return future.result(timeout=self.timeout)

    def run(self, agent_system: Any) -> dict[str, Any]:
        results = []
        for case in self.evaluator.test_cases:
            question = case.get("question", "")
            expected = case.get("answer", "").strip().lower()
            start = time.monotonic()
            try:
                response = self._execute_with_timeout(
                    self.evaluator._call_agent, agent_system, question
                )
            except Exception as e:  # pragma: no cover - defensive guard
                end = time.monotonic()
                results.append(
                    {
                        "question": question,
                        "error": str(e),
                        "success": False,
                        "response_time": end - start,
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
        pass_rate = (
            sum(1 for r in results if r["success"]) / len(results) if results else 0.0
        )
        avg_time = (
            statistics.mean(r["response_time"] for r in results) if results else 0.0
        )
        return {
            "total_cases": len(results),
            "passed": sum(1 for r in results if r.get("success")),
            "pass_rate": pass_rate,
            "average_time": avg_time,
            "results": results,
        }


def main() -> None:  # pragma: no cover - CLI utility
    dataset = (
        Path(__file__).resolve().parents[2]
        / "benchmarks"
        / "browsecomp"
        / "dataset_v1.json"
    )
    harness = IntegrationTestHarness(str(dataset))

    def echo_agent(question: str) -> str:
        return question  # placeholder agent

    report = harness.run(echo_agent)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
