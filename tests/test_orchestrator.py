import yaml

from engine.orchestrator import Orchestrator, Planner, Reflector, Stage
from tools.adapters import ToolCall


def test_lifecycle_transitions(monkeypatch):
    planner = Planner()
    reflector = Reflector()
    orch = Orchestrator(planner, reflector)

    def fake_execute(call: ToolCall):
        return {"tool": call.name, "args": call.args}

    monkeypatch.setattr("tools.adapters.execute", fake_execute)

    result = orch.run_task("find info")

    assert orch.history == [
        Stage.IDLE,
        Stage.PLAN,
        Stage.EXECUTE,
        Stage.REFLECT,
        Stage.COMPLETE,
    ]
    assert "search" in result
    assert "read" in result


def test_planner_outputs_yaml():
    planner = Planner()
    plan = planner.plan("research quantum")
    data = yaml.safe_load(plan)
    assert isinstance(data, list)
    assert any(n.get("depends") for n in data)
