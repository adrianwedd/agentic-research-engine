import pytest

from agents.evaluator import EvaluatorAgent
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService

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


class _DummyProcedural:
    def __init__(self) -> None:
        self.storage = InMemoryStorage()


def test_query_risk_cases_returns_similar_first():
    service = LTMService(
        EpisodicMemoryService(InMemoryStorage()),
        procedural_memory=_DummyProcedural(),
    )
    agent = EvaluatorAgent(ltm_service=service)

    critique1 = {
        "prompt": "How to make a cake",
        "outcome": "risk",
        "risk_categories": ["harm"],
        "overall_score": 0.2,
        "criteria_breakdown": {"accuracy": 0.2},
        "feedback_text": "danger",
        "created_at": 1.0,
        "updated_at": 1.0,
    }
    critique2 = {
        "prompt": "Tell me a joke",
        "outcome": "ok",
        "risk_categories": ["none"],
        "overall_score": 0.9,
        "criteria_breakdown": {"accuracy": 1.0},
        "feedback_text": "good",
        "created_at": 1.0,
        "updated_at": 1.0,
    }
    service.store_evaluator_memory(critique1)
    service.store_evaluator_memory(critique2)

    results = agent.query_risk_cases("How can I make a cake step by step?", limit=2)
    assert results
    prompts = [
        r.get("prompt")
        or r.get("task_context", {}).get("prompt")
        or r.get("outcome", {}).get("prompt")
        for r in results
    ]
    assert any("cake" in (p or "").lower() for p in prompts)
