from __future__ import annotations

"""Simple code execution tool using a subprocess sandbox."""

import subprocess
import sys
from typing import List


def code_interpreter(
    code: str, *, args: List[str] | None = None, timeout: int = 5
) -> dict:
    """Execute ``code`` as a Python script with optional ``args``.

    Parameters
    ----------
    code: str
        Python code to execute.
    args: List[str] | None
        Command line arguments available as ``sys.argv[1:]``.
    timeout: int
        Maximum execution time in seconds.

    Returns
    -------
    dict
        Mapping with ``stdout``, ``stderr``, and ``returncode`` fields.
    """
    if not isinstance(code, str):
        raise ValueError("code must be a string")
    cmd = [sys.executable, "-"]
    if args:
        cmd.extend(args)
    try:
        proc = subprocess.run(
            cmd,
            input=code,
            text=True,
            capture_output=True,
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
