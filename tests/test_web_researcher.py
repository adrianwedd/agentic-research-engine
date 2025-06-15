from agents.web_researcher import WebResearcherAgent


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
