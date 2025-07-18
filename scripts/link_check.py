#!/usr/bin/env python3
"""Run markdown-link-check on all markdown files.

This script is a thin wrapper around `markdown-link-check` executed via `npx`.
It scans provided paths (files or directories) for `.md` files and checks each
with `markdown-link-check`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_check(file: Path) -> int:
    """Run markdown-link-check on a single file."""
    print(f"Checking {file}")
    result = subprocess.run(
        ["npx", "--yes", "markdown-link-check", "--quiet", str(file)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(result.stdout)
    return result.returncode


def gather_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(path.rglob("*.md"))
        elif path.suffix == ".md":
            files.append(path)
    return files


def main(paths: list[str]) -> int:
    files = gather_files(paths)
    rc = 0
    for f in files:
        rc |= run_check(f)
    return rc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Markdown links with markdown-link-check"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["README.md", "docs"],
        help="Files or directories to scan",
    )
    args = parser.parse_args()
    sys.exit(main(args.paths))
