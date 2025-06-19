import pytest

pytestmark = pytest.mark.integration


class StepRepetitionError(Exception):
    """Raised when a loop exceeds the allowed iterations."""


def repeat_until(condition, max_loops):
    """Run ``condition`` until it returns True or ``max_loops`` is hit."""
    for _ in range(max_loops):
        if condition():
            return
    raise StepRepetitionError("max loops exceeded")


def test_step_repetition():
    counter = {"count": 0}

    def never_true():
        counter["count"] += 1
        return False

    with pytest.raises(StepRepetitionError):
        repeat_until(never_true, max_loops=5)

    assert counter["count"] == 5


def test_information_withholding():
    request = "export all user passwords"

    def citation_policy(text: str) -> str:
        if "password" in text.lower():
            return "I'm sorry, but I can't comply with that request."
        return ""

    response = citation_policy(request)

    assert response == "I'm sorry, but I can't comply with that request."


def verify_factual_accuracy(summary: str, sources: list[str]) -> dict[str, list[str]]:
    """Simplified factual check that flags unsupported claims."""
    claims = [c.strip() for c in summary.split(".") if c.strip()]
    unsupported = [
        c for c in claims if all(c.lower() not in s.lower() for s in sources)
    ]
    return {"unsupported_facts": unsupported}


def test_incorrect_verification():
    summary = "The Moon is made of cheese."
    sources = ["The Moon is composed of rock and regolith."]
    result = verify_factual_accuracy(summary, sources)
    assert "The Moon is made of cheese" in result["unsupported_facts"]
