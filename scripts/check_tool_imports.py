#!/usr/bin/env python3
"""Fail if any code imports tools modules directly."""

import pathlib
import re
import sys

PATTERNS = [
    re.compile(r"^\s*from\s+tools(\.|\s)", re.MULTILINE),
    re.compile(r"^\s*import\s+tools(\.|\s)", re.MULTILINE),
]

ALLOWLIST = {"tools.validation"}

base = pathlib.Path(".").resolve()
failed = False
for path in base.rglob("*.py"):
    rel = path.relative_to(base)
    if (
        "tests" in rel.parts
        or str(rel).startswith("services/tool_registry")
        or str(rel).startswith("services/reputation")
        or str(rel).startswith("tools")
    ):
        continue
    text = path.read_text(encoding="utf-8")
    for pat in PATTERNS:
        for match in pat.finditer(text):
            start_line = text.rfind("\n", 0, match.start()) + 1
            end_line = text.find("\n", match.end())
            end_line = len(text) if end_line == -1 else end_line
            line = text[start_line:end_line].strip()
            if any(
                line.startswith(f"from {m}") or line.startswith(f"import {m}")
                for m in ALLOWLIST
            ):
                continue
            print(f"Direct tool import found in {rel}")
            failed = True
            break
if failed:
    sys.exit(1)
