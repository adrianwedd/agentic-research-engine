"""CLI for listing open Codex tasks from the queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import yaml

DEFAULT_QUEUE = Path(".codex/queue.yml")


def load_suggested_tasks(path: str | Path = DEFAULT_QUEUE) -> List[Dict[str, str]]:
    """Return tasks without a 'done' status from the queue."""
    queue_path = Path(path)
    if not queue_path.exists():
        return []

    with queue_path.open() as f:
        data = yaml.safe_load(f) or []

    tasks: List[Dict[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", "")).lower()
        if status == "done":
            continue
        tid = entry.get("id")
        title = entry.get("title")
        if tid and title:
            tasks.append({"id": tid, "title": title})
    return tasks


def main(argv: List[str] | None = None) -> None:
    """Print suggested tasks to stdout in JSON format."""
    parser = argparse.ArgumentParser(description="Print suggested Codex tasks")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    args = parser.parse_args(argv)
    tasks = load_suggested_tasks(args.queue)
    json.dump(tasks, fp=sys.stdout)


if __name__ == "__main__":  # pragma: no cover
    main()
