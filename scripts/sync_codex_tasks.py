"""Validate that .codex/queue.yml matches open Codex issues on GitHub.

Environment Variables
---------------------
GITHUB_REPOSITORY
    Repository in the form ``owner/repo``. If not set, the script attempts
    to infer the repository from the current Git remote.
GITHUB_TOKEN
    Optional token used for authenticated API requests.
"""

import os
import re
import subprocess
import sys
from typing import List

import requests
import yaml

GITHUB_API = "https://api.github.com"


def guess_repo_from_git() -> str | None:
    """Return the "owner/repo" string from the current Git remote."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
    except Exception:
        return None
    url = result.stdout.strip()
    m = re.search(r"github\.com[/:]([\w.-]+/[\w.-]+)(?:\.git)?$", url)
    return m.group(1) if m else None


def load_queue_ids(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = yaml.safe_load(f) or []
    return [t.get("id") for t in data if isinstance(t, dict) and t.get("id")]


def fetch_issue_ids(repo: str, token: str | None = None) -> List[str]:
    url = f"{GITHUB_API}/repos/{repo}/issues?state=open&per_page=100"
    headers = {"Authorization": f"token {token}"} if token else {}
    ids: List[str] = []
    while url:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code >= 300:
            print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
            return []
        for issue in resp.json():
            labels = {lbl.get("name", "").lower() for lbl in issue.get("labels", [])}
            if "codex-task" in labels or "codex task" in labels:
                m = re.search(r"([A-Z]+-[0-9]+)", issue.get("title", ""))
                if m:
                    ids.append(m.group(1))
        url = resp.links.get("next", {}).get("url")
    return ids


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY") or guess_repo_from_git()
    token = os.environ.get("GITHUB_TOKEN")
    if not repo:
        print(
            "GITHUB_REPOSITORY not set and repository could not be determined. "
            "Set the environment variable with 'export GITHUB_REPOSITORY=owner/repo' "
            "to check open Codex issues.",
            file=sys.stderr,
        )
        return 1

    queue_ids = load_queue_ids(os.path.join(".codex", "queue.yml"))
    issue_ids = fetch_issue_ids(repo, token)

    missing = [i for i in issue_ids if i not in queue_ids]
    extra = [i for i in queue_ids if i not in issue_ids]

    if missing or extra:
        print("Codex task synchronization issues detected:")
        if missing:
            print(
                "  Tasks present in issues but missing from queue:",
                ", ".join(sorted(missing)),
            )
        if extra:
            print(
                "  Tasks present in queue with no open issue:", ", ".join(sorted(extra))
            )
        return 1

    print("Codex task queue synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
