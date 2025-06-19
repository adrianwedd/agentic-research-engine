import pytest

from agents.code_researcher import CodeResearcherAgent
from agents.web_researcher import WebResearcherAgent
from services.tool_registry import AccessDeniedError, ToolRegistry


@pytest.mark.core
def test_webresearcher_blocked_tool():
    registry = ToolRegistry()
    registry.register_tool("web_search", lambda q: [], allowed_roles=["Supervisor"])
    registry.register_tool("summarize", lambda t: "", allowed_roles=["WebResearcher"])
    with pytest.raises(AccessDeniedError):
        WebResearcherAgent(registry).research_topic("topic", {})


@pytest.mark.core
def test_code_researcher_blocked_tool():
    registry = ToolRegistry()
    registry.register_tool(
        "code_interpreter", lambda c, args=None: {}, allowed_roles=["Supervisor"]
    )
    agent = CodeResearcherAgent(registry)
    with pytest.raises(AccessDeniedError):
        agent.analyze_code("print('hi')")
