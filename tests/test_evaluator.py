import pytest

from agents.evaluator import EvaluatorAgent

pytestmark = pytest.mark.core


def test_verify_factual_accuracy_flags_unsupported():
    calls = []

    def fake_llm(prompt: str) -> str:
        calls.append(prompt)
        return "no"

    agent = EvaluatorAgent(fact_check_llm=fake_llm)
    summary = "Cats can fly."
    sources = ["Dogs bark loudly."]
    result = agent.verify_factual_accuracy(summary, sources)
    assert "Cats can fly." in result["unsupported_facts"]
    assert len(calls) == 1


def test_verify_factual_accuracy_accepts_supported():
    def fake_llm(prompt: str) -> str:
        return "yes"

    agent = EvaluatorAgent(fact_check_llm=fake_llm)
    summary = "Dogs bark."
    sources = ["Dogs bark loudly."]
    result = agent.verify_factual_accuracy(summary, sources)
    assert result["unsupported_facts"] == []


def test_assess_source_quality_penalizes_blocklist():
    agent = EvaluatorAgent()
    output = {"sources": ["http://clickbait.com/article"]}
    results = agent.evaluate_research_output(output, {"source_quality": {}})
    score = results["source_quality"]["scores"]["http://clickbait.com/article"]
    assert score < 0


def test_assess_source_quality_rewards_allowlist():
    agent = EvaluatorAgent()
    output = {"sources": ["https://jstor.org/paper"]}
    results = agent.evaluate_research_output(output, {"source_quality": {}})
    score = results["source_quality"]["scores"]["https://jstor.org/paper"]
    assert score > 0
