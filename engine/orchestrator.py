from __future__ import annotations

"""Simplified orchestrator with state machine and tool adapters."""

from dataclasses import dataclass, field
from enum import Enum
from importlib import import_module
from typing import Any, Dict, List

import yaml
from opentelemetry import trace

from .planner import Planner
from .reflector import Reflector


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


@dataclass
class Orchestrator:
    planner: Planner
    reflector: Reflector
    history: List[Stage] = field(default_factory=list)

    def run_task(self, prompt: str) -> Dict[str, Any]:
        self.history.append(Stage.IDLE)
        with tracer.start_as_current_span("plan"):
            self.history.append(Stage.PLAN)
            plan = self.planner.plan(prompt)
        with tracer.start_as_current_span("execute"):
            self.history.append(Stage.EXECUTE)
            result = self._execute_plan(plan.as_yaml())
        with tracer.start_as_current_span("reflect"):
            self.history.append(Stage.REFLECT)
            reflection = self.reflector.reflect(result)
            result["feedback"] = reflection.text
        with tracer.start_as_current_span("complete"):
            self.history.append(Stage.COMPLETE)
        return result

    def _execute_plan(self, plan_yaml: str) -> Dict[str, Any]:
        data = yaml.safe_load(plan_yaml)
        steps = data if isinstance(data, list) else data.get("steps", [])
        outputs = {}
        for node in steps:
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
