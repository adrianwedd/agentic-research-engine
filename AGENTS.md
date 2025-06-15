# AGENTS.md

## Code Style
- Use **Black** and **isort** for formatting Python code. Configure flake8 with max-line-length 120 and ignore E203. Run `pre-commit run --all-files` before committing.

## Testing
- Run tests with `pytest -q`.
- Execute `pre-commit run --all-files` to run linters and formatters.

## Setup
- Run `bash scripts/agent-setup.sh` to install Python dependencies and pre-commit hooks.

## PR Guidelines
- Summarize changes in the PR description.
- Include test results in the PR body.
- Ensure all tests and linters pass before opening a pull request.
