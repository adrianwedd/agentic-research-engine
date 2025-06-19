from __future__ import annotations

"""Lightweight planner producing YAML DAG plans."""

from dataclasses import dataclass
from typing import List

import yaml

PLANNER_TEMPLATE = """\
# Plan for: {prompt}
steps:
- id: search
  tool: web.search
  args:
    query: "{prompt}"
- id: read
  tool: pdf.reader
  depends: [search]
  args:
    path_or_url: "{{search[0].url}}"
"""


@dataclass
class Plan:
    text: str

    def as_yaml(self) -> str:
        return self.text

    def tasks(self) -> List[str]:
        data = yaml.safe_load(self.text)
        return [n["id"] for n in data.get("steps", [])]


class Planner:
    """Generate a simple multi-step plan."""

    template: str = PLANNER_TEMPLATE

    def plan(self, prompt: str) -> Plan:
        plan_text = self.template.format(prompt=prompt)
        return Plan(text=plan_text)
