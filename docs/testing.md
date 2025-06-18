# Testing Overview

This project uses `pytest` for unit and integration tests. A set of contract tests ensures the LTM service HTTP API remains stable.

## Running Tests

Use `pytest` to execute the suite:

```bash
pytest -q
```

Run linters with `pre-commit`:

```bash
pre-commit run --all-files
```

## Running Core Tests Only

To quickly verify essential functionality, run only the tests marked `core`:

```bash
pytest -m "core"
```

This skips any tests labeled `optional` and the heavier integration suite.

## Contract Tests

Contract tests live in `tests/test_ltm_contract.py` and load scenarios from JSON fixtures in `tests/fixtures/ltm_contract/`. Each fixture defines the request headers, body and the expected response. The helper `_assert_contract` checks that status codes and response fields match the fixture.

To update fixtures when the API changes:

1. Modify or add files in `tests/fixtures/ltm_contract/` with the new expected schema.
2. Update any corresponding tests to load the new fixtures.
3. Run the tests to verify they pass.

CI will fail if any endpoint response deviates from these contracts, helping detect breaking API changes early.
