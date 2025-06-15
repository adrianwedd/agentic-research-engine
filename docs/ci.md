# Continuous Integration Guidelines

This project uses GitHub Actions to run tests and code quality checks on every pull request.
The main workflow is defined in `.github/workflows/ci.yml` and ensures that all
linters pass and the full test suite runs with coverage enabled.

## Coverage Gates

All test jobs invoke `pytest` with the `pytest-cov` plugin. The workflow fails if
overall coverage drops below **80%**. Coverage results are stored in `coverage.xml`
and uploaded as a workflow artifact. Developers should run the following before
pushing changes:

```bash
pytest --cov=./ --cov-report=xml --cov-fail-under=80
```

This mirrors the CI behaviour so local failures can be detected early.

