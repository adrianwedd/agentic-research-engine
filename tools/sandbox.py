from __future__ import annotations

"""Lightweight sandbox for executing Python code securely."""

import os
import subprocess
import sys
import tempfile
import textwrap
from typing import List

_WRAPPER_TEMPLATE = """
import resource
import socket
import sys

# Apply resource limits
resource.setrlimit(resource.RLIMIT_CPU, ({timeout}, {timeout}))
resource.setrlimit(resource.RLIMIT_AS, ({memory}, {memory}))

# Disable all network access
class _BlockedSocket(socket.socket):
    def __new__(cls, *args, **kwargs):
        raise OSError('network access disabled')

socket.socket = _BlockedSocket  # type: ignore[assignment]
socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(OSError('network access disabled'))

code_file = sys.argv[1]
args = sys.argv[2:]
with open(code_file) as f:
    code = f.read()

sys.argv = [sys.argv[0]] + args
exec(compile(code, '<sandbox>', 'exec'), {{'__name__': '__main__'}})
"""


def run_python_code(
    code: str,
    *,
    args: List[str] | None = None,
    timeout: int = 5,
    memory_limit_mb: int = 128,
) -> dict:
    """Execute ``code`` inside a restricted subprocess."""
    if not isinstance(code, str):
        raise ValueError("code must be a string")

    args = args or []

    with tempfile.TemporaryDirectory() as tmp:
        code_path = os.path.join(tmp, "code.py")
        wrapper_path = os.path.join(tmp, "wrapper.py")
        with open(code_path, "w") as f:
            f.write(code)
        with open(wrapper_path, "w") as f:
            script = _WRAPPER_TEMPLATE.format(
                timeout=timeout, memory=memory_limit_mb * 1024 * 1024
            )
            f.write(textwrap.dedent(script))

        cmd = [sys.executable, wrapper_path, code_path] + list(args)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "timeout expired", "returncode": -1}
