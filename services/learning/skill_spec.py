"""Generate and parse skill specifications via LLM prompts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from services.llm_client import LLMClient
from services.ltm_service.skill_library import SkillLibrary


@dataclass
class SkillSpec:
    """Structured description of a skill."""

    name: str
    termination_condition: str
    reward_function: str


def parse_skill_specs(text: str) -> List[SkillSpec]:
    """Parse JSON text into a list of :class:`SkillSpec`."""
    data = json.loads(text)
    specs: List[SkillSpec] = []
    for item in data.get("sub_tasks", []):
        specs.append(
            SkillSpec(
                name=item.get("name", ""),
                termination_condition=item.get("termination_condition", ""),
                reward_function=item.get("reward_function", ""),
            )
        )
    return specs


def generate_skill_specs(
    task: str, *, llm: LLMClient, template: str
) -> List[SkillSpec]:
    """Use ``llm`` and ``template`` to produce skill specs for ``task``."""
    prompt = template.format(task=task)
    text = llm.invoke([{"role": "user", "content": prompt}])
    return parse_skill_specs(text)


def store_skill_specs(specs: List[SkillSpec], library: SkillLibrary) -> List[str]:
    """Persist specs in ``library`` as skills with metadata."""
    ids: List[str] = []
    for spec in specs:
        sid = library.add_skill(
            {"policy": []},
            spec.name,
            {
                "skill_spec": {
                    "name": spec.name,
                    "termination_condition": spec.termination_condition,
                    "reward_function": spec.reward_function,
                }
            },
        )
        ids.append(sid)
    return ids


def load_default_template() -> str:
    """Return the built-in SkillSpecAgent prompt template."""
    path = (
        Path(__file__).resolve().parents[2]
        / "agents"
        / "SkillSpecAgent"
        / "prompt.tpl.md"
    )
    return path.read_text()


def generate_skill_specs_from_agent(
    task: str, *, llm: LLMClient, template_path: str | None = None
) -> List[SkillSpec]:
    """Convenience wrapper that loads the default template and parses specs."""

    if template_path:
        template = Path(template_path).read_text()
    else:
        template = load_default_template()
    return generate_skill_specs(task, llm=llm, template=template)
