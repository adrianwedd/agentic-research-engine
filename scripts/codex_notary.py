import os
import sys
from typing import List

import yaml

from scripts import issue_logger

GITHUB_API = "https://api.github.com"


def load_queue(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = yaml.safe_load(f) or []
    return [d for d in data if isinstance(d, dict)]


def save_queue(path: str, tasks: List[dict]) -> None:
    with open(path, "w") as f:
        yaml.safe_dump(tasks, f, sort_keys=False)


def create_issues_for_queue(queue_path: str, repo: str) -> int:
    tasks = load_queue(queue_path)
    changed = False
    for t in tasks:
        if t.get("issue_id"):
            continue
        title = f"{t.get('id')}: {t.get('title', '')}".strip()
        body_parts: List[str] = []
        if t.get("strategic_rationale"):
            body_parts.append(f"**Strategic Rationale**\n{t['strategic_rationale']}")
        if t.get("detailed_description"):
            body_parts.append(f"**Detailed Description**\n{t['detailed_description']}")
        body = "\n\n".join(body_parts)
        labels: List[str] = []
        if t.get("phase"):
            labels.append(f"phase:{t['phase']}")
        if t.get("epic"):
            labels.append(f"epic:{t['epic']}")
        result = issue_logger.create_issue(title, body, repo, labels=labels)
        if not result:
            print(f"Failed to create issue for {t.get('id')}", file=sys.stderr)
            return 1
        if result.get("number"):
            t["issue_id"] = int(result["number"])
            changed = True
        else:
            print(f"Issue creation response missing number: {result}", file=sys.stderr)
            return 1
    if changed:
        save_queue(queue_path, tasks)
    return 0


def main(argv: List[str] | None = None) -> int:
    queue_path = argv[0] if argv else os.path.join(".codex", "queue.yml")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("GITHUB_REPOSITORY not set", file=sys.stderr)
        return 1
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not set", file=sys.stderr)
        return 1
    return create_issues_for_queue(queue_path, repo)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
