import pytest

from agents.code_researcher import CodeResearcherAgent
from engine.orchestration_engine import GraphState

pytestmark = pytest.mark.core


def test_analyze_code_invokes_interpreter():
    calls = []

    def interpreter(code: str, *, args=None, timeout=5):
        calls.append(code)
        return {"stdout": "ok", "stderr": "", "returncode": 0}

    agent = CodeResearcherAgent({"code_interpreter": interpreter})
    result = agent.analyze_code("print('hi')")

    assert result["stdout"] == "ok"
    assert calls == ["print('hi')"]


def test_node_updates_state():
    def interpreter(code: str, *, args=None, timeout=5):
        return {"stdout": "done", "stderr": "", "returncode": 0}

    agent = CodeResearcherAgent({"code_interpreter": interpreter})
    state = GraphState(data={"code": "print('x')", "code_args": []})
    out = agent(state, {})

    assert out.data["code_result"]["stdout"] == "done"
