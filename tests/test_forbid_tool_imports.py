import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/check_tool_imports.py").resolve()


def test_detects_direct_tool_import(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("from tools.html_scraper import html_scraper\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True
    )
    assert "Direct tool import found in bad.py" in result.stdout
    assert result.returncode == 1
