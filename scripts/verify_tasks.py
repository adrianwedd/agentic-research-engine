#!/usr/bin/env python3
"""Fail if tasks marked done lack repository evidence."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

EXCLUDE_PATHS = ["tasks.yml", "docs/reviews/tasks_verification_report.md"]


def search_repo(pattern: str) -> bool:
    cmd = [
        "git",
        "grep",
        "-l",
        pattern,
        "--",
    ] + [f":(exclude){p}" for p in EXCLUDE_PATHS]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return bool(result.stdout.strip())


def task_has_evidence(task: dict) -> bool:
    for pat in [str(task.get("task_id", "")), str(task.get("title", ""))]:
        if pat and search_repo(pat):
            return True
    return False


def main() -> int:
    tasks_file = Path("tasks.yml")
    tasks = yaml.safe_load(tasks_file.read_text())
    missing: list[dict] = []
    for task in tasks:
        if str(task.get("status", "")).lower() == "done":
            if not task_has_evidence(task):
                missing.append(task)
    if missing:
        print("Tasks marked done but lacking evidence:")
        for t in missing:
            print(f"- {t.get('task_id')} {t.get('title')}")
        return 1
    print("All done tasks have evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
