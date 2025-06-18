import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

from agents.critique import CRITIQUE_SCHEMA, Critique


def test_schema_file_fields():
    path = Path("agents/evaluator/config/critique_schema.json")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data.get("required", [])) == {
        "prompt",
        "outcome",
        "risk_categories",
        "created_at",
        "updated_at",
        "overall_score",
        "criteria_breakdown",
        "feedback_text",
    }
    props = data.get("properties", {})
    assert props.get("overall_score", {}).get("type") == "number"
    assert props.get("criteria_breakdown", {}).get("type") == "object"
    assert props.get("feedback_text", {}).get("type") == "string"


def test_critique_validation_passes():
    crit = Critique(
        prompt="p",
        outcome="pass",
        risk_categories=["test"],
        overall_score=0.8,
        criteria_breakdown={"accuracy": 0.9},
        feedback_text="ok",
        created_at=1.0,
        updated_at=1.0,
    )
    crit.validate()


def test_critique_validation_fails():
    bad = {"overall_score": 2}
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=CRITIQUE_SCHEMA)
