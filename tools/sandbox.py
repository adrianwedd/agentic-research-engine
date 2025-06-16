from __future__ import annotations

"""Lightweight sandbox for executing Python code securely."""

import json
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

result_file = sys.argv[1]
code_file = sys.argv[2]
args = sys.argv[3:]
with open(code_file) as f:
    code = f.read()

import ast
import json

tree = ast.parse(code, mode='exec')
if tree.body and isinstance(tree.body[-1], ast.Expr):
    expr = tree.body[-1]
    tree.body[-1] = ast.Assign(targets=[ast.Name("_result", ast.Store())], value=expr.value)
    ast.fix_missing_locations(tree)
    has_result = True
else:
    has_result = False
    ast.fix_missing_locations(tree)
code_obj = compile(tree, "<sandbox>", "exec")

sys.argv = [sys.argv[0]] + args
env = {{'__name__': '__main__'}}
exec(code_obj, env)
if has_result:
    with open(result_file, 'w') as rf:
        json.dump(env.get('_result'), rf)
else:
    open(result_file, 'w').write('null')
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
        result_path = os.path.join(tmp, "result.json")
        with open(code_path, "w") as f:
            f.write(code)
        with open(wrapper_path, "w") as f:
            script = _WRAPPER_TEMPLATE.format(
                timeout=timeout, memory=memory_limit_mb * 1024 * 1024
            )
            f.write(textwrap.dedent(script))

        cmd = [sys.executable, wrapper_path, result_path, code_path] + list(args)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            try:
                with open(result_path) as rf:
                    result = json.load(rf)
            except Exception:
                result = None
            return {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode,
                "result": result,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "timeout expired",
                "returncode": -1,
                "result": None,
            }
