# Judge Rubric Examples

This document illustrates valid objects that conform to `schemas/judge_rubric.json`.

## Example 1: Scores Only
```json
{
  "schema_version": "1.0",
  "factual_accuracy": {"score": 1.0},
  "completeness": {"score": 0.9},
  "source_quality": {"score": 1.0},
  "coherence": {"score": 0.8}
}
```

## Example 2: Scores with Justifications
```json
{
  "schema_version": "1.0",
  "factual_accuracy": {"score": 0.8, "justification": "Minor factual slips"},
  "completeness": {"score": 1.0, "justification": "All points addressed"},
  "source_quality": {"score": 0.9, "justification": "Some sources are blog posts"},
  "coherence": {"score": 1.0, "justification": "Clear and logical flow"}
}
```
