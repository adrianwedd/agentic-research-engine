# Contributing

Thank you for helping improve this project! The repository uses a generated task queue located at `.codex/queue.yml`. Tasks are defined in `codex_tasks.md` using fenced code blocks tagged `codex-task`.

Example block:

```codex-task
id: CODEX-EXAMPLE-02
title: "Write docs"
priority: medium
steps:
  - draft text
acceptance_criteria:
  - docs committed
```

To regenerate the queue file after editing `codex_tasks.md` run:

```bash
python scripts/codex_task_runner.py
```

Useful flags:

- `--from <ID>` — only rebuild tasks with IDs greater than or equal to `ID`.
- `--preview` — print the resulting YAML to stdout instead of writing to `.codex/queue.yml`.

The CI pipeline verifies that the queue file matches the tasks. Ensure you run the script before opening a pull request.

## Branch Protection

All development happens on feature branches. Direct pushes to `main` are disabled.
Pull requests targeting `main` must have at least one approved review and pass all
required CI status checks before they can be merged. These settings are enforced
through the repository's branch protection rules.

To confirm the configuration, you can run `scripts/check_branch_protection.py`.
The script calls the GitHub API and returns non-zero if the rules are missing or
incomplete.

## Environment Setup

Create a virtual environment or use the repository's devcontainer before installing dependencies:

```bash
python -m venv .venv && source .venv/bin/activate
bash scripts/agent-setup.sh
```

The setup script installs CPU-only PyTorch by default. Optional packages like `langsmith` and `trl` can be installed separately.

## Secrets Management

API keys and credentials should never be committed to the repository. Use a dedicated secrets manager such as **HashiCorp Vault** or **AWS Secrets Manager** to store these values. Retrieve them at runtime and expose the results as environment variables.

### Example: HashiCorp Vault

1. Store your keys in Vault:

   ```bash
   vault kv put secret/agentic \
       SEARCH_API_KEY=<your-search-key> \
       FACT_CHECK_API_KEY=<your-fact-check-key>
   ```

2. Export the values before running the tools:

   ```bash
   export SEARCH_API_KEY=$(vault kv get -field=SEARCH_API_KEY secret/agentic)
   export FACT_CHECK_API_KEY=$(vault kv get -field=FACT_CHECK_API_KEY secret/agentic)
   ```

You can source these commands from a setup script or run `vault agent` to template an `.env` file automatically. See [docs/security.md](docs/security.md) for more details.

## Pre-commit Hooks

Formatting and linting are enforced with `pre-commit`. Install the tool and set
up the git hooks after cloning:

```bash
pip install pre-commit
pre-commit install
```

Before submitting a pull request run:

```bash
pre-commit run --all-files
```

This will apply `black`, `flake8`, and `isort` to your changes.

## Pre-PR Testing

Before opening a pull request, verify your changes locally.
Tests are tagged into three categories:

- **core** – fast unit tests that cover critical functionality
- **integration** – tests that exercise service boundaries or heavy components
- **optional** – slow or environment-specific checks

Run the lightweight **core** test suite to verify basic functionality:

```bash
pytest -m "core" -q
```

You can also run `bash scripts/test_core.sh` as a shorthand. The command should complete quickly and exit with code `0`.

To execute the full suite (all `core`, `integration`, and `optional` tests) run:

```bash
pytest -q
```

Any failures must be fixed prior to submission.

Then execute the pre-commit hooks on all files:

```bash
pre-commit run --all-files
```

This step formats the codebase and runs lint checks.

## Docs Structure

Project documentation lives in the `docs/` folder. Academic papers and surveys
go under `docs/research/` and should follow the naming pattern
`YYYY-<short-slug>.md`. Phase-based deliverables such as security audits or
performance scorecards belong in `docs/reports/` with filenames like
`phase<phase#>-<topic>-report.md`. Remember to update `mkdocs.yml` so the new
page appears in the navigation sidebar.

## Release Process

1. Update `infra/helm/agent-services/Chart.yaml` with the new version.
2. Tag the commit and push the tag:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

   Pushing the tag triggers the `.github/workflows/cd.yml` pipeline. The
   workflow builds the container image and deploys it to the `staging`
   environment.
3. After verifying staging, run the `promote-production` workflow from the
   GitHub Actions UI to deploy the same image to production.

Release artifacts consist of the container image and the packaged Helm chart.
