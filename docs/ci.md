# Continuous Integration Guidelines

This project uses GitHub Actions to run tests and code quality checks on every pull request via the `minimal-ci.yml` workflow.
The full workflow defined in `.github/workflows/ci.yml` runs when changes are merged to `main` (or on the nightly schedule) and ensures that all linters pass and the complete test suite runs with coverage enabled.

## Coverage Gates

All test jobs invoke `pytest` with the `pytest-cov` plugin. The workflow fails if
overall coverage drops below **80%**. Coverage results are stored in `coverage.xml`
and uploaded as a workflow artifact. Developers should run the following before
pushing changes:

```bash
pytest --cov=./ --cov-report=xml --cov-fail-under=80
```

This mirrors the CI behaviour so local failures can be detected early.

## Failure Summaries

Each CI run ends with a concise summary block that shows the tail of the test
log and the overall coverage percentage. Direct links to the coverage HTML
report and full logs are included. Failing tests are annotated inline in the PR
using the `pytest-github-actions-annotate-failures` plugin.

Example:

```
## Test Failure Summary

**Coverage:** 82.3%

<last lines from tests.log>

[Coverage HTML](https://github.com/org/repo/actions/runs/<run_id>#artifacts)
[Full Log](https://github.com/org/repo/actions/runs/<run_id>)
```

Download the `coverage-html` artifact from the run and open `index.html` locally
to view detailed coverage results.

