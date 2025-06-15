#!/usr/bin/env python3
"""Fail if any code imports tools modules directly."""

import pathlib
import re
import sys

PATTERNS = [
    re.compile(r"^\s*from\s+tools(\.|\s)"),
    re.compile(r"^\s*import\s+tools(\.|\s)"),
]

base = pathlib.Path(".").resolve()
failed = False
for path in base.rglob("*.py"):
    rel = path.relative_to(base)
    if (
        "tests" in rel.parts
        or str(rel).startswith("services/tool_registry")
        or str(rel).startswith("tools")
    ):
        continue
    text = path.read_text(encoding="utf-8")
    for pat in PATTERNS:
        if pat.search(text, re.MULTILINE):
            print(f"Direct tool import found in {rel}")
            failed = True
            break
if failed:
    sys.exit(1)
