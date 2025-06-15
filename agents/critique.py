from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from jsonschema import validate

SCHEMA_PATH = (
    Path(__file__).resolve().parent / "evaluator" / "config" / "critique_schema.json"
)
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    CRITIQUE_SCHEMA: Dict[str, Any] = json.load(f)


@dataclass
class Critique:
    """Structured critique produced by the Evaluator agent."""

    overall_score: float
    criteria_breakdown: Dict[str, float]
    feedback_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "criteria_breakdown": self.criteria_breakdown,
            "feedback_text": self.feedback_text,
        }

    def validate(self) -> None:
        """Validate this critique against the JSON schema."""

        validate(instance=self.to_dict(), schema=CRITIQUE_SCHEMA)
