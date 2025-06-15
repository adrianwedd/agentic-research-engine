# Judge Pipeline Contract Tests

This directory contains contract tests for the LLM-as-a-Judge evaluation pipeline.
The tests ensure that given a known report, the pipeline produces JSON matching
`schemas/judge_rubric.json` and persists the result.

## Running the tests

Execute the tests directly with `pytest`:

```bash
pytest pipelines/judge/tests -v
```

## Adding new cases

1. Create a JSON fixture under `pipelines/judge/tests/fixtures/` named
   `caseN.json` (increment `N`). Each fixture should include the `report` text and
   a `scores` object representing the expected rubric scores.
2. The contract test will load fixtures in sorted order and feed each set of
   scores through a fake LLM. Extend the fixtures to cover new behaviours or edge
   cases.

## Interpreting failures

A failing test prints a diff between the expected scores from the fixture and the
actual pipeline output or the jsonschema validation error. The CI summary also
includes the tail of the test log for quick debugging.
