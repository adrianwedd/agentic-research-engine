import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def coverage_percent(xml_path: str) -> str:
    path = Path(xml_path)
    if not path.is_file():
        return "N/A"
    root = ET.parse(path).getroot()
    rate = root.get("line-rate")
    if rate is None:
        return "N/A"
    return f"{float(rate) * 100:.1f}%"


def tail_lines(log_path: str, num: int = 20) -> str:
    path = Path(log_path)
    if not path.is_file():
        return "log file missing"
    return "\n".join(path.read_text().splitlines()[-num:])


def main(log_path: str = "tests.log", cov_path: str = "coverage.xml") -> int:
    summary_file = Path(os.environ.get("GITHUB_STEP_SUMMARY", ""))
    cov = coverage_percent(cov_path)
    tail = tail_lines(log_path)
    text = [
        "## Test Failure Summary",
        "",
        f"**Coverage:** {cov}",
        "",
        "```",
        tail,
        "```",
        "",
        (
            f"[Coverage HTML](https://github.com/{os.environ.get('GITHUB_REPOSITORY')}/"
            f"actions/runs/{os.environ.get('GITHUB_RUN_ID')}#artifacts)"
        ),
        (
            f"[Full Log](https://github.com/{os.environ.get('GITHUB_REPOSITORY')}/"
            f"actions/runs/{os.environ.get('GITHUB_RUN_ID')})"
        ),
    ]
    if summary_file:
        summary_file.write_text("\n".join(text))
    else:
        print("\n".join(text))
    return 0


if __name__ == "__main__":
    sys.exit(main(*(sys.argv[1:3])))
