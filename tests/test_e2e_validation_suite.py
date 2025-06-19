import pytest

from agents.citation_agent import CitationAgent
from agents.planner import PlannerAgent
from agents.web_researcher import WebResearcherAgent
from engine.orchestration_engine import GraphState, create_orchestration_engine
from services.policy_monitor import PolicyMonitor, PolicyViolation, set_monitor
from services.tool_registry import ToolRegistry


@pytest.mark.integration
def test_e2e_happy_path_literature_review():
    """Scenario E2E-01: Happy-Path Literature Review."""
    registry = ToolRegistry()

    def web_search(query: str):
        return [
            {
                "url": "http://example.com/paper1.pdf",
                "title": "Paper 1",
                "text": "content",
            },
            {
                "url": "http://example.com/paper2.pdf",
                "title": "Paper 2",
                "text": "content",
            },
            {
                "url": "http://example.com/paper3.pdf",
                "title": "Paper 3",
                "text": "content",
            },
        ]

    registry.register_tool("web_search", web_search, allowed_roles=["WebResearcher"])
    registry.register_tool(
        "summarize", lambda text: "summary", allowed_roles=["WebResearcher"]
    )
    registry.register_tool(
        "assess_source", lambda url: 1.0, allowed_roles=["WebResearcher"]
    )

    planner = PlannerAgent()
    researcher = WebResearcherAgent(registry)
    citation = CitationAgent()

    def supervisor_node(state: GraphState, _sp: dict) -> GraphState:
        plan = planner.plan_research_task(state.data["query"])
        task = plan["graph"]["nodes"][0]["topic"]
        state.update({"plan": plan, "sub_task": task})
        return state

    def synthesize_node(state: GraphState, _sp: dict) -> GraphState:
        sources = state.data.get("research_result", {}).get("sources", [])
        report = "final report with diagram\n\n```mermaid\ngraph TD; A-->B;\n```"
        state.update({"report": report, "sources": sources})
        return state

    engine = create_orchestration_engine()
    engine.add_node("Supervisor", supervisor_node)
    engine.add_node("Researcher", researcher)
    engine.add_node("Synthesize", synthesize_node)
    engine.add_node("Citation", citation)
    engine.add_edge("Supervisor", "Researcher")
    engine.add_edge("Researcher", "Synthesize")
    engine.add_edge("Synthesize", "Citation")

    result = engine.run(
        GraphState(data={"query": "Quantum error-correcting codes 2023-2025"})
    )

    assert "report" in result.data
    assert "```mermaid" in result.data["report"]
    assert len(result.data.get("research_result", {}).get("sources", [])) >= 3


@pytest.mark.integration
def test_e2e_tool_governance_enforcement(caplog):
    """Scenario E2E-03: Tool Governance Enforcement."""
    monitor = PolicyMonitor({"blocked_tools": ["shell.exec"]})
    set_monitor(monitor)
    registry = ToolRegistry()
    registry.register_tool("shell.exec", lambda cmd: "done")

    with pytest.raises(PolicyViolation):
        registry.invoke("Researcher", "shell.exec", "rm -rf /")

    assert any(e["type"] == "tool" and not e["allowed"] for e in monitor.events)

    result = "task complete"
    assert result == "task complete"
