
# Security Guidelines

This guide describes how to monitor RBAC failures in the Tool Registry.

## Viewing RBAC Logs

`ToolRegistryServer` logs every failed authorization attempt as a JSON record. Run the server normally and check its standard logs or your configured log aggregator.

Example log entry:

```json
{"timestamp": "2024-01-01T12:00:00Z", "role": "Supervisor", "tool": "dummy", "user": "alice", "client_ip": "127.0.0.1", "path": "/tool?agent=Supervisor&name=dummy", "error": "Role 'Supervisor' cannot access tool 'dummy'"}
```

Fields:

- `timestamp` – UTC time of the request
- `role` – agent role making the request
- `tool` – requested tool name
- `user` – identity of the caller if provided
- `client_ip` – IP address of the client
- `path` – HTTP path and query
- `error` – reason access was denied

Use `docker compose logs tool-registry` or your monitoring backend to search for these records and audit failed access attempts.



This document outlines how to handle secrets and API keys for the agentic-research-engine.

This document outlines security practices for the Agentic Research Engine.

## Dependency Audit Schedule

To monitor third-party vulnerabilities, a weekly audit runs on the first business day (Monday) of each week.

1. **Update dependencies**
   - Run `pip install --upgrade -r requirements.txt` to update packages.
   - Commit any changes to `requirements.txt` or generated lock files.
2. **Run the scan**
   - Execute `pip-audit -r requirements.txt -o pip_audit_report.json`.
   - Review the report for new vulnerabilities.
3. **Triage findings**
   - Open or update an issue summarizing any new CVEs and plan remediation.
   - If no issues are found, note the successful audit in the issue tracker.

Push the updates and open a pull request to trigger CI. The scheduled workflow runs `pip-audit` automatically and creates an issue if new vulnerabilities are detected.


## Secrets Management

The project uses external APIs for web search and fact checking. The corresponding keys (`SEARCH_API_KEY` and `FACT_CHECK_API_KEY`) must never be committed to the repository.
Store these values in a dedicated secrets manager such as **HashiCorp Vault**, **AWS Secrets Manager**, or your preferred provider. At runtime the secrets manager should populate the required environment variables.

### Local development

Retrieve the secrets from the manager and export them before running the application. An optional `.env` file can be used during local testing:

```bash
SEARCH_API_KEY=... # retrieved from your secrets manager
FACT_CHECK_API_KEY=...
```

Load the variables with `source .env` or a tool like `direnv`.

### CI configuration

In GitHub Actions, add the keys as repository secrets and expose them in the workflow:

```yaml
jobs:
  tests:
    env:
      SEARCH_API_KEY: ${{ secrets.SEARCH_API_KEY }}
      FACT_CHECK_API_KEY: ${{ secrets.FACT_CHECK_API_KEY }}
```

See `.github/workflows/ci.yml` for the job structure (environment variables are defined starting at line 13).

### Production deployments

Configure your deployment scripts to pull secrets from the manager and inject them into the container or runtime environment. A Docker Compose example:

```yaml
services:
  app:
    environment:
      SEARCH_API_KEY: ${SEARCH_API_KEY}
      FACT_CHECK_API_KEY: ${FACT_CHECK_API_KEY}
```

### Key rotation and revocation

Use your secrets manager's versioning features to rotate keys without downtime. When a secret is compromised:

1. Revoke the old version in the manager.
2. Update the new key in CI and deployment settings.
3. Restart running services to pick up the change.

### Code references

The tools read API keys from environment variables:

- [`tools/web_search.py`](../tools/web_search.py) lines 27–45
- [`tools/fact_check.py`](../tools/fact_check.py) lines 26–46

Environment variable injection in CI happens in [`ci.yml`](../.github/workflows/ci.yml) starting around line 13.

# Dependency Security Scanning

The CI workflow includes a job named `security:dependencies` that checks project dependencies for known vulnerabilities using **pip-audit**.

The job runs on every pull request and pushes to `main`. A report is generated at `security/pip_audit_report.json` and uploaded as a workflow artifact.

## Interpreting the Report

1. Download the artifact from the workflow run.
2. Open `pip_audit_report.json` and inspect the listed vulnerabilities.
3. The job fails when any vulnerability with a severity of **high** or **critical** is detected. Lower-severity issues are reported but do not block the build.
4. Update affected packages to resolve vulnerabilities. Rerun the scan to verify.

## Running Locally

```bash
pip install pip-audit
pip-audit -r requirements.txt -f json -o security/pip_audit_report.json
python scripts/check_pip_audit.py security/pip_audit_report.json
```

The script exits with a non-zero status if high or critical vulnerabilities are present.

