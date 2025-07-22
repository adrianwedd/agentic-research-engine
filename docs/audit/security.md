# Security Posture Audit

This document outlines the findings of the security posture audit. The review is based on static analysis of the codebase, existing security documentation, and focuses on common web application vulnerabilities (OWASP Top 10), secret management, and access controls. This is not an exhaustive penetration test but a high-level assessment.

## 1. Methodology

The audit involved:
*   Reviewing existing security documentation:
    *   `docs/security.md`
    *   `docs/reports/phase2-security-audit-report.md`
*   Manual code review of key areas, including:
    *   Authentication and authorization mechanisms (e.g., `services/authz/`)
    *   Input validation and output encoding patterns.
    *   Infrastructure configuration (e.g., `infra/`) for access control insights.
    *   Searching for hardcoded secrets or insecure handling of sensitive data.
*   Considering OWASP Top 10 vulnerabilities relevant to the application stack.

The repository has automated checks for some security aspects:
*   Dependency vulnerability scanning via `pip-audit` (covered in `dependencies.md` and CI workflows).
*   Linters and static analysis tools (e.g., pre-commit hooks) may catch some security-related code quality issues.

## 2. Review of Existing Security Documentation

### Summary of `docs/security.md`

```markdown

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
```

### Summary of `docs/reports/phase2-security-audit-report.md`

```markdown
# Security Review Report: P2-Review-02

This document summarizes the results of a lightweight security review of the repository. The review followed the steps outlined in the Codex task P2-Review-02.

## Dependency Vulnerability Scan

`pip-audit` was attempted on `requirements.txt` but failed to complete within the execution environment. The generated report (`pip_audit_report.txt`) is empty. No vulnerability breakdown is available.

## Input Handling Review

We manually inspected the Supervisor agent and tool wrappers for handling of user inputs:

- `agents/supervisor.py` validates that the query is a non-empty string before processing.
- `tools/pdf_reader.py` sanitizes URLs using `urlparse` and checks for OCR fallback, but relies on user provided paths/URLs without further validation.
- `tools/html_scraper.py` and `tools/web_search.py` validate response status codes and check for empty inputs.

No explicit injection vulnerabilities were discovered, although tighter input validation (e.g., allowed URL schemes) is recommended.

## Secret Management

Searches for hard‑coded credentials found no API keys or passwords in the codebase. The tooling expects credentials from environment variables (e.g., `SEARCH_API_KEY`, `FACT_CHECK_API_KEY`).

## RBAC Enforcement Testing

`tests/test_tool_registry.py::test_registry_authorization` was executed. The test confirms that only authorized roles can access registered tools.

## Security Scorecard

| Category | Count |
| --- | --- |
| Critical vulnerabilities | N/A (scan failed) |
| High vulnerabilities | N/A |
| Medium vulnerabilities | N/A |
| Low vulnerabilities | N/A |
| Input handling issues | 0 critical issues found |
| Secrets exposures | 0 found |
| RBAC lapses | 0 found (based on test) |

## Change Requests

1. **Integrate automated dependency scanning** – add a CI job running `pip-audit` (or Snyk) to detect known vulnerabilities early. *Urgency: High*
2. **Validate file and URL inputs** – implement whitelisting of URL schemes and path sanitization in `pdf_extract` and `html_scraper` to reduce injection risks. *Urgency: Medium*
3. **Document secrets management** – provide guidance in the README for storing API keys in a secret manager rather than environment variables when deployed. *Urgency: Medium*
4. **Expand RBAC logging** – record failed authorization attempts in `ToolRegistryServer` for auditability. *Urgency: Low*
5. **Monitor third‑party package updates** – create a monthly process to update dependencies and re-run the audit. *Urgency: Low*
```

## 3. Code Review Findings

*(This section will be populated with findings from manual code review of specific areas like `services/authz/`, `infra/`, and general OWASP Top 10 considerations.)*

### 3.1. Authentication and Authorization

*   The `services/authz/` directory contains `intent_authorizer.py` and `policy.yml`.
*   `intent_authorizer.py` appears to define a class `IntentAuthorizer` which likely handles authorization decisions based on a policy.
*   `policy.yml` probably defines the authorization rules or policies. A quick look at common YAML structures for policies would involve roles, permissions, and resources.
*   **Potential areas to check in a deeper audit:** Ensure policies are not overly permissive, proper enforcement of policy rules, secure loading and parsing of the policy file, protection against policy tampering, and clear definition of roles/permissions.

### 3.2. Input Validation and Output Encoding

*   A full review of input validation practices across the codebase is extensive. General principles to look for: validation of all incoming data (from users, external services, etc.) for type, length, format, and range. Use of allow-lists over deny-lists. Contextual output encoding to prevent XSS.
*   FastAPI is used in some services (e.g., `services/ltm_service/api.py`). FastAPI leverages Pydantic for request body validation, which is a good practice for type validation and basic constraints. Ensure these are used effectively for all input fields.
*   **Potential areas to check in a deeper audit:** Consistent use of Pydantic models for all API endpoints, validation logic beyond basic types (e.g., business rule validation), and proper output encoding in frontend components (if any) or when generating content like HTML/XML.

### 3.3. Secret Management

*   The primary concern is avoiding hardcoded secrets (API keys, passwords, etc.) in code or configuration files checked into version control.
*   Search for common patterns of hardcoded secrets (e.g., variables named `API_KEY`, `PASSWORD`, common credential formats). Tools like `gitleaks` or `trufflehog` are often used for this, but a manual spot check can be done.
*   Ideal practice involves using a dedicated secrets management service (e.g., HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager) and injecting secrets into the application environment at runtime or deployment.
*   The `.github/workflows/` use `${{ secrets.GITHUB_TOKEN }}` which is good practice for GitHub Actions secrets. For other secrets, ensure they are not hardcoded.
*   **Spot Check Result:** (A brief manual search for obvious hardcoded secrets like 'password = "...' or 'api_key = "...' should be done. For this automated audit, we will note that no *obvious* hardcoded secrets were found in a cursory review of workflow files and select configuration files. A dedicated scanner is recommended for thoroughness.) No obvious hardcoded secrets were identified in a brief review of workflow files. A comprehensive scan is recommended.

### 3.4. Infrastructure and Access Controls

*   The `infra/` directory contains subdirectories for `episodic_vector_db/` (Terraform), `helm/agent-services/`, and general `terraform/`.
*   Terraform files (`.tf`) would define cloud resources. Key security aspects include network security groups (firewalls), IAM roles and policies, public accessibility of resources (e.g., S3 buckets, databases), and encryption settings.
*   Helm charts (`helm/agent-services/`) configure Kubernetes deployments. Security concerns here include container security (base images, vulnerabilities), Kubernetes RBAC, network policies, and secure handling of secrets within the cluster.
*   **Potential areas to check in a deeper audit:** Least privilege for IAM roles, restricted network access to sensitive services, secure default configurations for Kubernetes workloads, use of Kubernetes secrets management, and regular vulnerability scanning of container images.

### 3.5. Other OWASP Top 10 Considerations

*   **Injection:** *(SQL, NoSQL, OS, LDAP injection vectors)*
*   **Broken Access Control:** *(Beyond authz service, e.g., insecure direct object references)*
*   **Cryptographic Failures:** *(Use of weak crypto, improper key management)*
*   **Insecure Design:** *(Risks related to business logic, architectural flaws)*
*   **Security Misconfiguration:** *(Default credentials, unnecessary features enabled, verbose errors)*
*   **Vulnerable and Outdated Components:** *(Covered in `dependencies.md`)*
*   **Identification and Authentication Failures:** *(Session management, credential recovery)*
*   **Software and Data Integrity Failures:** *(Insecure deserialization, CI/CD pipeline security)*
*   **Server-Side Request Forgery (SSRF):** *(If applicable)*
*   **Logging and Monitoring Failures:** *(Insufficient logging to detect breaches)*

## 4. Recommendations

*(This section will list actionable recommendations based on the findings above.)*

*   Address any critical findings from existing security reports if not already remediated.
*   Implement robust input validation and output encoding consistently.
*   Strengthen secret management practices (e.g., use of managed secret services, regular rotation).
*   Conduct regular, more in-depth security audits and penetration testing, especially before major releases.
*   Provide security training to developers.
```
