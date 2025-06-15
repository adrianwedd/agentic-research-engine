from scripts.check_pip_audit import is_high, iter_vulnerabilities

sample_report = {
    "dependencies": [
        {
            "name": "foo",
            "version": "1.0",
            "vulns": [
                {"id": "CVE-123", "severity": "high"},
                {"id": "CVE-456", "severity": "low"},
            ],
        }
    ]
}

def test_detect_high_vulnerability():
    vulns = list(iter_vulnerabilities(sample_report))
    assert any(is_high(v) for v in vulns)

