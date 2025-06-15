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
