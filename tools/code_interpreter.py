from __future__ import annotations

"""Simple code execution tool leveraging the sandbox module."""

from typing import List

from .sandbox import run_python_code


def code_interpreter(
    code: str,
    *,
    args: List[str] | None = None,
    timeout: int = 5,
    memory_limit_mb: int = 128,
) -> dict:
    """Execute ``code`` with optional ``args`` in an isolated sandbox."""

    return run_python_code(
        code, args=args or [], timeout=timeout, memory_limit_mb=memory_limit_mb
    )
