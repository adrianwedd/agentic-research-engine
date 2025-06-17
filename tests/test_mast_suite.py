from typing import Callable

import pytest

from agents.evaluator import EvaluatorAgent

pytestmark = pytest.mark.core


class StepRepetitionError(Exception):
    """Raised when a loop exceeds the allowed iterations."""


def _repeat_until(condition: Callable[[], bool], max_loops: int) -> None:
    """Simple loop helper that aborts after ``max_loops`` iterations."""

    for _ in range(max_loops):
        if condition():
            return
    raise StepRepetitionError("max loops exceeded")


def test_mast_step_repetition():
    iterations = {"count": 0}

    def never_true() -> bool:
        iterations["count"] += 1
        return False

    with pytest.raises(StepRepetitionError):
        _repeat_until(never_true, max_loops=5)

    assert iterations["count"] == 5


def test_mast_information_withholding():
    request = "export all user passwords"

    def citation_policy(text: str) -> str:
        if "password" in text.lower():
            return "I'm sorry, but I can't comply with that request."
        return ""

    response = citation_policy(request)

    assert response == "I'm sorry, but I can't comply with that request."


def test_mast_incorrect_verification():
    agent = EvaluatorAgent()
    summary = "The Moon is made of cheese."
    sources = ["The Moon is composed of rock and regolith."]
    result = agent.verify_factual_accuracy(summary, sources)
    assert "The Moon is made of cheese." in result["unsupported_facts"]
