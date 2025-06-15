import json
from pathlib import Path

from jsonschema import Draft7Validator, validate


def load_schema():
    path = Path("schemas/judge_rubric.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_is_valid():
    schema = load_schema()
    Draft7Validator.check_schema(schema)
    props = schema.get("properties", {})
    assert set(
        [
            "schema_version",
            "factual_accuracy",
            "completeness",
            "source_quality",
            "coherence",
        ]
    ).issubset(props)


def test_sample_validates():
    schema = load_schema()
    sample = {
        "schema_version": "1.0",
        "factual_accuracy": {"score": 1.0},
        "completeness": {"score": 0.9},
        "source_quality": {"score": 0.8},
        "coherence": {"score": 1.0},
    }
    validate(instance=sample, schema=schema)
