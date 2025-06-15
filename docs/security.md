# Security Guidelines

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
