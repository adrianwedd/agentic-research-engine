"""Integration test harness for BrowseComp benchmarks."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import statistics
import time
from pathlib import Path
from typing import Any, Callable

from .browsecomp_evaluator import BrowseCompEvaluator


class IntegrationTestHarness:
    """Run the BrowseComp benchmark with per-question timeouts."""

    def __init__(
        self,
        dataset_path: str,
        *,
        timeout: float | None = None,
        retries: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        timeout_val = (
            float(os.getenv("HARNESS_TIMEOUT", "30")) if timeout is None else timeout
        )
        retries_val = (
            int(os.getenv("HARNESS_RETRIES", "0")) if retries is None else retries
        )

        delay_val = (
            float(os.getenv("HARNESS_RETRY_DELAY", "0.1"))
            if retry_delay is None
            else retry_delay
        )

        self.evaluator = BrowseCompEvaluator(dataset_path)
        self.timeout = timeout_val
        self.retries = retries_val
        self.retry_delay = delay_val

    def _execute_with_timeout(self, func: Callable[..., Any], *args: Any) -> Any:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(func, *args)
            return future.result(timeout=self.timeout)

    def run(self, agent_system: Any) -> dict[str, Any]:
        results = []
        logger = logging.getLogger(__name__)
        for case in self.evaluator.test_cases:
            question = case.get("question", "")
            expected = case.get("answer", "").strip().lower()
            start = time.monotonic()
            attempt = 0
            timed_out = False
            error = None
            response = None
            while attempt <= self.retries:
                try:
                    response = self._execute_with_timeout(
                        self.evaluator._call_agent, agent_system, question
                    )
                    if attempt:
                        logger.info(
                            "question '%s' succeeded after %d attempt(s)",
                            question,
                            attempt + 1,
                        )
                    break
                except concurrent.futures.TimeoutError:
                    timed_out = True
                    logger.warning(
                        "timeout on question '%s' (attempt %d/%d)",
                        question,
                        attempt + 1,
                        self.retries + 1,
                    )
                except Exception as e:  # pragma: no cover - defensive guard
                    error = str(e)
                    logger.warning(
                        "error on question '%s' (attempt %d/%d): %s",
                        question,
                        attempt + 1,
                        self.retries + 1,
                        e,
                    )
                attempt += 1
                if attempt <= self.retries:
                    time.sleep(self.retry_delay)
                else:
                    break
            end = time.monotonic()

            if response is None:
                logger.error(
                    "question '%s' failed: %s",
                    question,
                    error or f"timeout after {self.timeout}s",
                )
                results.append(
                    {
                        "question": question,
                        "error": error or f"timeout after {self.timeout}s",
                        "timed_out": timed_out,
                        "success": False,
                        "response_time": end - start,
                    }
                )
                continue

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
                    "timed_out": timed_out,
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
