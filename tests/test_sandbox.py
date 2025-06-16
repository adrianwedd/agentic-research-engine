import importlib.util
import pathlib

import pytest

spec = importlib.util.spec_from_file_location(
    "sandbox", pathlib.Path("tools/sandbox.py")
)
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)  # type: ignore
run_python_code = sandbox.run_python_code

pytestmark = pytest.mark.core


def test_network_blocked():
    code = "import urllib.request\nurllib.request.urlopen('http://example.com')"
    result = run_python_code(code, timeout=2)
    assert result["returncode"] != 0
    assert "network access disabled" in result["stderr"]


def test_timeout_enforced():
    code = "while True:\n    pass"
    result = run_python_code(code, timeout=1)
    assert result["returncode"] != 0
    assert "timeout" in result["stderr"]
