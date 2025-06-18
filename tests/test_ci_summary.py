from scripts import ci_summary


def test_main_writes_summary(tmp_path, monkeypatch):
    log_file = tmp_path / "tests.log"
    log_file.write_text("line1\nline2\nline3\n")

    cov_file = tmp_path / "coverage.xml"
    cov_file.write_text('<coverage line-rate="0.8"/>')

    summary_file = tmp_path / "summary.txt"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setenv("GITHUB_REPOSITORY", "u/r")
    monkeypatch.setenv("GITHUB_RUN_ID", "1")

    exitcode = ci_summary.main(str(log_file), str(cov_file))
    assert exitcode == 0

    text = summary_file.read_text()
    assert "**Coverage:** 80.0%" in text
    assert "line2" in text and "line3" in text
