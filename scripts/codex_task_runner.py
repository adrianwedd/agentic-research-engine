import argparse
import os
import re
import sys
from typing import Any, Dict, List

import yaml

BLOCK_RE = re.compile(r"```codex-task\n(.*?)\n```", re.DOTALL)
REQUIRED_FIELDS = {"id", "title", "priority", "steps", "acceptance_criteria"}


def parse_tasks(md_text: str) -> List[Dict[str, Any]]:
    tasks = []
    seen_ids = set()
    for match in BLOCK_RE.findall(md_text):
        try:
            data = yaml.safe_load(match)
        except Exception as e:
            excerpt = "\n".join(match.splitlines()[:5])
            print(
                f"YAML parse error in block:\n{excerpt}\n{e}",
                file=sys.stderr,
            )
            continue
        if not isinstance(data, dict):
            print(
                f"Invalid block (not a mapping): {match[:30]}",
                file=sys.stderr,
            )
            continue
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            print(
                f"Missing fields {missing} in task {data.get('id')}",
                file=sys.stderr,
            )
            continue
        if data["id"] in seen_ids:
            print(
                f"Duplicate ID {data['id']} found; skipping",
                file=sys.stderr,
            )
            continue
        seen_ids.add(data["id"])
        tasks.append(data)
    return tasks


def load_queue(path: str) -> List[Dict[str, Any]]:
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or []
            if not isinstance(data, list):
                print(
                    f"Queue at {path} is not a list",
                    file=sys.stderr,
                )
                return []
            return data
    return []


def save_queue(path: str, tasks: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(tasks, f)


def merge_tasks(
    existing: List[Dict[str, Any]],
    new_tasks: List[Dict[str, Any]],
    from_id: str | None,
) -> List[Dict[str, Any]]:
    id_to_index = {t["id"]: i for i, t in enumerate(existing)}
    for t in new_tasks:
        if from_id and t["id"] < from_id:
            continue
        if t["id"] in id_to_index:
            print(
                f"Duplicate ID {t['id']} already in queue; skipping",
                file=sys.stderr,
            )
            continue
        existing.append(t)
    return existing


def main():
    parser = argparse.ArgumentParser(
        description="Generate .codex/queue.yml from codex_tasks.md"
    )
    parser.add_argument(
        "--from",
        dest="from_id",
        help="only process tasks with id >= given",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="print output instead of writing",
    )
    args = parser.parse_args()

    with open("codex_tasks.md") as f:
        md_text = f.read()
    tasks = parse_tasks(md_text)

    queue_path = os.path.join(".codex", "queue.yml")
    existing = load_queue(queue_path)
    merged = merge_tasks(existing, tasks, args.from_id)

    if args.preview:
        yaml.safe_dump(merged, sys.stdout)
    else:
        save_queue(queue_path, merged)


if __name__ == "__main__":
    main()
