from __future__ import annotations

"""Simplified orchestrator with state machine and tool adapters."""

from dataclasses import dataclass, field
from enum import Enum
from importlib import import_module
from typing import Any, Dict, List

import yaml
from opentelemetry import trace


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]


def _dispatch(call: ToolCall):
    adapters = import_module("tools.adapters")
    return adapters.execute(call)


tracer = trace.get_tracer(__name__)


class Stage(str, Enum):
    IDLE = "IDLE"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    REFLECT = "REFLECT"
    COMPLETE = "COMPLETE"


class Planner:
    """Very small planning stub generating a fixed DAG."""

    template = """- id: search\n  tool: web.search\n- id: read\n  tool: pdf.reader\n  depends: [search]\n"""

    def plan(self, prompt: str) -> str:
        del prompt
        return self.template


class Reflector:
    """Stub reflection module."""

    def reflect(self, result: Dict[str, Any]) -> str:
        _ = result
        return "ok"


@dataclass
class Orchestrator:
    planner: Planner
    reflector: Reflector
    history: List[Stage] = field(default_factory=list)

    def run_task(self, prompt: str) -> Dict[str, Any]:
        self.history.append(Stage.IDLE)
        with tracer.start_as_current_span("plan"):
            self.history.append(Stage.PLAN)
            plan_yaml = self.planner.plan(prompt)
        with tracer.start_as_current_span("execute"):
            self.history.append(Stage.EXECUTE)
            result = self._execute_plan(plan_yaml)
        with tracer.start_as_current_span("reflect"):
            self.history.append(Stage.REFLECT)
            feedback = self.reflector.reflect(result)
            result["feedback"] = feedback
        with tracer.start_as_current_span("complete"):
            self.history.append(Stage.COMPLETE)
        return result

    def _execute_plan(self, plan_yaml: str) -> Dict[str, Any]:
        plan = yaml.safe_load(plan_yaml)
        outputs = {}
        for node in plan:
            tool = node["tool"]
            name = node["id"]
            deps = node.get("depends", [])
            args = (
                {"query": "test"}
                if tool == "web.search"
                else {"path_or_url": "http://example.com/dummy.pdf"}
            )
            for dep in deps:
                outputs.setdefault(name, []).append(outputs.get(dep))
            call = ToolCall(name=tool, args=args)
            outputs[name] = _dispatch(call)
        return outputs
