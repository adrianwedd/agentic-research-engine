import pytest

from agents.citation_agent import CitationAgent
from engine.orchestration_engine import GraphState

pytestmark = pytest.mark.core


def test_citation_agent_formats_apa():
    agent = CitationAgent()
    source = {
        "author": "Smith",
        "title": "AI Research",
        "year": 2024,
        "url": "http://example.com",
    }
    apa = agent._format_citation(source, "APA")
    assert "Smith" in apa and "2024" in apa


def test_citation_agent_inserts_citations():
    agent = CitationAgent()
    report = "Cats purr."
    sources = [
        {
            "text": "Cats often purr when happy.",
            "author": "Jones",
            "title": "Felines",
            "year": 2023,
            "url": "http://cats.com",
        }
    ]
    state = GraphState(data={"report": report, "sources": sources})
    out = agent(state, {})
    assert "cats.com" in out.data["citations"][0]
    assert "(" in out.data["report"]
