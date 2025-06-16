import pytest

from agents.web_researcher import WebResearcherAgent
from engine.orchestration_engine import GraphState

pytestmark = pytest.mark.core


def test_research_topic_uses_tools():
    calls = {}

    def track(name):
        def wrapper(*args, **kwargs):
            calls.setdefault(name, 0)
            calls[name] += 1
            return f"{name}_result"

        return wrapper

    def web_search(query):
        return [
            {"url": "http://example.com/doc.pdf", "title": "Doc"},
            {"url": "http://example.com/page", "title": "Page"},
        ]

    def pdf_extract(url):
        assert url.endswith(".pdf")
        return "pdf text"

    def html_scraper(url):
        assert url.endswith("page")
        return "html text"

    registry = {
        "web_search": web_search,
        "pdf_extract": pdf_extract,
        "html_scraper": html_scraper,
        "summarize": track("summarize"),
        "assess_source": lambda url: 0.9,
    }

    agent = WebResearcherAgent(registry)
    result = agent.research_topic("test topic", {})

    assert result["topic"] == "test topic"
    assert len(result["sources"]) == 2
    assert result["confidence"] == 0.9
    assert calls["summarize"] == 2


def test_summarize_to_state_adds_message():
    def summarize(text):
        return "summary"

    registry = {"web_search": lambda q: [], "summarize": summarize}
    agent = WebResearcherAgent(registry)

    from engine.state import State

    state = State(data={"raw_text": "word " * 5000, "task": "topic"})
    agent.summarize_to_state(state)

    assert state.messages[-1]["content"] == "summary"


def test_webresearcher_node_executes_query():
    queries: list[str] = []

    def web_search(q: str):
        queries.append(q)
        return []

    registry = {
        "web_search": web_search,
        "summarize": lambda text: "",
        "pdf_extract": None,
        "html_scraper": None,
        "assess_source": lambda url: 1.0,
    }

    agent = WebResearcherAgent(registry)
    state = GraphState(
        data={"sub_task": "find papers on Transformer architecture", "agent_id": "A"}
    )
    result = agent(state)

    assert queries, "web_search was not called"
    q = queries[0].lower()
    assert "transformer architecture" in q
    assert "academic papers" in q
    assert "research_result" in result.data


def test_research_topic_retries_and_errors():
    calls: list[int] = []

    def web_search(q: str):
        return [{"url": "http://example.com/doc.pdf", "title": "Doc"}]

    def failing_pdf(url: str):
        calls.append(1)
        raise ValueError("boom")

    registry = {
        "web_search": web_search,
        "pdf_extract": failing_pdf,
        "html_scraper": None,
        "summarize": lambda text: "summary",
        "assess_source": lambda url: 1.0,
    }

    agent = WebResearcherAgent(registry, max_retries=2)
    with pytest.raises(RuntimeError):
        agent.research_topic("topic", {})

    assert len(calls) == 2


def test_webresearcher_prefers_knowledge_graph():
    calls: list[str] = []

    def kg_search(query: dict) -> list:
        calls.append("kg")
        return [{"subject": "France", "predicate": "HAS_CAPITAL", "object": "Paris"}]

    def web_search(q: str) -> list:
        calls.append("web")
        return []

    registry = {
        "web_search": web_search,
        "knowledge_graph_search": kg_search,
        "pdf_extract": None,
        "html_scraper": None,
        "summarize": lambda text: "",
        "assess_source": lambda url: 1.0,
    }

    agent = WebResearcherAgent(registry)
    result = agent.research_topic("capital of France", {})

    assert calls[0] == "kg"
    assert "web" not in calls
    assert result["facts"][0]["object"] == "Paris"
