# Security Guidelines

This document outlines how to handle secrets and API keys for the agentic-research-engine.

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
