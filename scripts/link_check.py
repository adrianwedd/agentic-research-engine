#!/usr/bin/env python3
"""Run `lychee` on all Markdown files.

This script is a lightweight wrapper around the `lychee` link checker. It scans
the provided paths (files or directories) for ``.md`` files and checks them in a
single ``lychee`` invocation.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_check(files: list[Path]) -> int:
    """Run lychee on a list of files."""
    if shutil.which("lychee") is None:
        print(
            "lychee is not installed. Install it with `cargo install lychee`.",
            file=sys.stderr,
        )
        return 1

    cmd = [
        "lychee",
        "--no-progress",
        "--max-redirects",
        "5",
        "--dump",
    ] + [str(f) for f in files]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


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
    if not files:
        print("No markdown files found", file=sys.stderr)
        return 1
    return run_check(files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Markdown links using lychee")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["README.md", "docs"],
        help="Files or directories to scan",
    )
    args = parser.parse_args()
    sys.exit(main(args.paths))
