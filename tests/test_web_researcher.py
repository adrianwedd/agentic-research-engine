import base64
import importlib

import pytest

from agents.web_researcher import WebResearcherAgent
from engine.orchestration_engine import GraphState
from services.tool_registry import ToolRegistry
from tests.test_pdf_reader_tool import HELLO_PDF_B64
from tools.pdf_reader import pdf_extract as real_pdf_extract

html_scraper_module = importlib.import_module("tools.html_scraper")
real_html_scraper = html_scraper_module.html_scraper

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

    registry = ToolRegistry()
    registry.register_tool("web_search", web_search, allowed_roles=["WebResearcher"])
    registry.register_tool("pdf_extract", pdf_extract, allowed_roles=["WebResearcher"])
    registry.register_tool(
        "html_scraper", html_scraper, allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "summarize", track("summarize"), allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "assess_source", lambda url: 0.9, allowed_roles=["WebResearcher"]
    )

    agent = WebResearcherAgent(registry)
    result = agent.research_topic("test topic", {})

    assert result["topic"] == "test topic"
    assert len(result["sources"]) == 2
    assert result["confidence"] == 0.9
    assert calls["summarize"] == 2


def test_summarize_to_state_adds_message():
    def summarize(text):
        return "summary"

    registry = ToolRegistry()
    registry.register_tool("web_search", lambda q: [], allowed_roles=["WebResearcher"])
    registry.register_tool("summarize", summarize, allowed_roles=["WebResearcher"])
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

    registry = ToolRegistry()
    registry.register_tool("web_search", web_search, allowed_roles=["WebResearcher"])
    registry.register_tool(
        "summarize", lambda text: "", allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "assess_source", lambda url: 1.0, allowed_roles=["WebResearcher"]
    )

    agent = WebResearcherAgent(registry)
    state = GraphState(
        data={"sub_task": "find papers on Transformer architecture", "agent_id": "A"}
    )
    result = agent(state, {})

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

    registry = ToolRegistry()
    registry.register_tool("web_search", web_search, allowed_roles=["WebResearcher"])
    registry.register_tool("pdf_extract", failing_pdf, allowed_roles=["WebResearcher"])
    registry.register_tool(
        "summarize", lambda text: "summary", allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "assess_source", lambda url: 1.0, allowed_roles=["WebResearcher"]
    )

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

    registry = ToolRegistry()
    registry.register_tool("web_search", web_search, allowed_roles=["WebResearcher"])
    registry.register_tool(
        "knowledge_graph_search", kg_search, allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "summarize", lambda text: "", allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "assess_source", lambda url: 1.0, allowed_roles=["WebResearcher"]
    )

    agent = WebResearcherAgent(registry)
    result = agent.research_topic("capital of France", {})

    assert calls[0] == "kg"
    assert "web" not in calls
    assert result["facts"][0]["object"] == "Paris"


def test_webresearcher_parses_http(monkeypatch):
    html = "<html><body><article><p>Hello Web.</p></article></body></html>"
    pdf_bytes = base64.b64decode(HELLO_PDF_B64)

    def fake_get(url: str, timeout: int = 10, **_):
        class DummyResp:
            def __init__(
                self, *, text: str | None = None, content: bytes | None = None
            ) -> None:
                self.text = text or ""
                self.content = content or b""
                self.status_code = 200

            def raise_for_status(self) -> None:
                pass

        if url.endswith(".pdf"):
            return DummyResp(content=pdf_bytes)
        return DummyResp(text=html)

    monkeypatch.setattr(html_scraper_module.requests, "get", fake_get)
    pdf_module = importlib.import_module(real_pdf_extract.__module__)
    monkeypatch.setattr(pdf_module.requests, "get", fake_get)

    summaries: list[str] = []

    def summarize(text: str) -> str:
        summaries.append(text)
        return "summary"

    registry = ToolRegistry()
    registry.register_tool(
        "web_search",
        lambda q: [
            {"url": "http://example.com/doc.pdf", "title": "Doc"},
            {"url": "http://example.com/page", "title": "Page"},
        ],
        allowed_roles=["WebResearcher"],
    )
    registry.register_tool(
        "pdf_extract", real_pdf_extract, allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "html_scraper", real_html_scraper, allowed_roles=["WebResearcher"]
    )
    registry.register_tool("summarize", summarize, allowed_roles=["WebResearcher"])
    registry.register_tool(
        "assess_source", lambda url: 1.0, allowed_roles=["WebResearcher"]
    )

    agent = WebResearcherAgent(registry)
    result = agent.research_topic("topic", {})

    assert result["topic"] == "topic"
    assert len(result["sources"]) == 2
    assert result["confidence"] == 1.0
    assert any("Hello Web" in s for s in summaries)
    assert any("Hello PDF" in s for s in summaries)
