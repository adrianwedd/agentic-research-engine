from __future__ import annotations

"""Simplistic reflection loop."""

from dataclasses import dataclass
from typing import Dict

default_reflection_prompt = "Was the plan executed successfully? Answer yes or no."


@dataclass
class Reflection:
    text: str

    def decision(self) -> str:
        return self.text.strip().lower()


class Reflector:
    """Return feedback from execution results."""

    prompt: str = default_reflection_prompt

    def reflect(self, result: Dict[str, object]) -> Reflection:
        del result
        # For prototype we simply return 'yes'
        return Reflection(text="yes")
