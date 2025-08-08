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

ALLOWED_HOSTS = {allowed_hosts}

# Apply resource limits
resource.setrlimit(resource.RLIMIT_CPU, ({timeout}, {timeout}))
resource.setrlimit(resource.RLIMIT_AS, ({memory}, {memory}))

# Enforce optional network allowlist
_orig_connect = socket.socket.connect

def _patched_connect(self, address):
    host = address[0]
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = host
    if ALLOWED_HOSTS is None or ip not in ALLOWED_HOSTS:
        print("SandboxNetworkBlocked", file=sys.stderr)
        raise OSError(f"network access to {{ip}} blocked")
    return _orig_connect(self, address)

socket.socket.connect = _patched_connect  # type: ignore[assignment]

def _create_connection(address, *args, **kwargs):
    s = socket.socket()
    _patched_connect(s, address)
    return s

socket.create_connection = _create_connection

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
    allowed_hosts: List[str] | None = None,
) -> dict:
    """Execute ``code`` inside a restricted subprocess.

    Parameters
    ----------
    code:
        Python code to execute.
    args:
        Optional command-line arguments passed to the code.
    timeout:
        CPU time limit in seconds.
    memory_limit_mb:
        Maximum memory usage in megabytes.
    allowed_hosts:
        Optional list of IP addresses that the code is permitted to
        access. ``None`` disables all network access.
    """
    # Security validations
    if not isinstance(code, str):
        raise ValueError("code must be a string")
    
    if len(code) > 100000:  # 100KB limit
        raise ValueError("Code too large (max 100KB)")
    
    # Check for dangerous imports and patterns
    dangerous_patterns = [
        'import os', 'import subprocess', 'import sys', 'import shutil',
        'import glob', 'from os', 'from subprocess', 'from sys',
        '__import__', 'exec(', 'eval(', 'compile(', 'open(',
        'file(', 'input(', 'raw_input('
    ]
    
    code_lower = code.lower()
    for pattern in dangerous_patterns:
        if pattern in code_lower:
            raise ValueError(f"Dangerous pattern detected: {pattern}")
    
    # Validate timeout and memory limits
    if not isinstance(timeout, int) or timeout <= 0 or timeout > 30:
        raise ValueError("Timeout must be a positive integer <= 30 seconds")
    
    if not isinstance(memory_limit_mb, int) or memory_limit_mb <= 0 or memory_limit_mb > 512:
        raise ValueError("Memory limit must be a positive integer <= 512 MB")
    
    # Validate arguments
    if args:
        if not isinstance(args, list) or len(args) > 10:
            raise ValueError("Args must be a list with max 10 elements")
        for arg in args:
            if not isinstance(arg, str) or len(arg) > 1000:
                raise ValueError("Each arg must be a string with max 1000 characters")
            # Prevent shell injection
            if any(char in arg for char in [';', '&', '|', '`', '$', '(', ')']):
                raise ValueError("Arguments contain potentially dangerous characters")
    
    # Validate allowed hosts
    if allowed_hosts is not None:
        if not isinstance(allowed_hosts, list) or len(allowed_hosts) > 10:
            raise ValueError("Allowed hosts must be a list with max 10 elements")
        import ipaddress
        for host in allowed_hosts:
            try:
                ipaddress.ip_address(host)
            except ValueError:
                raise ValueError(f"Invalid IP address: {host}")

    args = args or []

    with tempfile.TemporaryDirectory() as tmp:
        code_path = os.path.join(tmp, "code.py")
        wrapper_path = os.path.join(tmp, "wrapper.py")
        result_path = os.path.join(tmp, "result.json")
        with open(code_path, "w") as f:
            f.write(code)
        with open(wrapper_path, "w") as f:
            script = _WRAPPER_TEMPLATE.format(
                timeout=timeout,
                memory=memory_limit_mb * 1024 * 1024,
                allowed_hosts=repr(allowed_hosts),
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
