from agents.web_researcher import WebResearcherAgent
from engine.orchestration_engine import GraphState


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
