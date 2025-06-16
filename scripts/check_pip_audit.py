import json
import sys
from pathlib import Path

HIGH_SEVERITIES = {"high", "critical"}


def iter_vulnerabilities(data):
    if isinstance(data, dict):
        if "dependencies" in data:
            for dep in data.get("dependencies", []):
                for vuln in dep.get("vulns", []):
                    yield vuln
        if "vulnerabilities" in data:
            for vuln in data.get("vulnerabilities", []):
                yield vuln


def is_high(vuln):
    sev = vuln.get("severity")
    if not sev:
        ratings = vuln.get("ratings", [])
        if ratings and isinstance(ratings[0], dict):
            sev = ratings[0].get("severity")
    if not sev:
        desc = vuln.get("description", "").lower()
        for level in HIGH_SEVERITIES | {"medium", "low"}:
            if f"severity is {level}" in desc:
                sev = level
                break
    return sev and sev.lower() in HIGH_SEVERITIES


def main(path: str = "security/pip_audit_report.json") -> int:
    report = Path(path)
    if not report.is_file():
        print(f"Report not found: {report}", file=sys.stderr)
        return 1
    data = json.loads(report.read_text())
    if any(is_high(v) for v in iter_vulnerabilities(data)):
        print("High or critical vulnerabilities detected", file=sys.stderr)
        return 1
    print("No high or critical vulnerabilities found")
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(sys.argv[1] if len(sys.argv) > 1 else "security/pip_audit_report.json")
    )
