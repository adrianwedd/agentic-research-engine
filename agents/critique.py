from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import validate

SCHEMA_PATH = (
    Path(__file__).resolve().parent / "evaluator" / "config" / "critique_schema.json"
)
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    CRITIQUE_SCHEMA: Dict[str, Any] = json.load(f)


@dataclass
class Critique:
    """Structured critique produced by the Evaluator agent."""

    prompt: str
    outcome: str
    risk_categories: List[str]
    overall_score: float
    criteria_breakdown: Dict[str, float]
    feedback_text: str
    created_at: float
    updated_at: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "outcome": self.outcome,
            "risk_categories": self.risk_categories,
            "overall_score": self.overall_score,
            "criteria_breakdown": self.criteria_breakdown,
            "feedback_text": self.feedback_text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def validate(self) -> None:
        """Validate this critique against the JSON schema."""

        validate(instance=self.to_dict(), schema=CRITIQUE_SCHEMA)
