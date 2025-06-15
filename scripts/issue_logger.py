import json
import os
import sys
from typing import List, Optional
from datetime import datetime

import requests

GITHUB_API = "https://api.github.com"
WORKLOG_PENDING_FILE = os.path.join("state", "worklog_pending.json")

def _get_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not set. Set the environment variable to enable issue logging.", file=sys.stderr)
        return None
    return token


def _comments_url(issue_or_pr_url: str) -> str:
    if "/pulls/" in issue_or_pr_url:
        issue_or_pr_url = issue_or_pr_url.replace("/pulls/", "/issues/")
    return f"{issue_or_pr_url}/comments"


def _store_pending_worklog(target: str, data: dict) -> None:
    os.makedirs(os.path.dirname(WORKLOG_PENDING_FILE), exist_ok=True)
    pending = []
    if os.path.exists(WORKLOG_PENDING_FILE):
        try:
            with open(WORKLOG_PENDING_FILE) as f:
                pending = json.load(f) or []
        except Exception:
            pending = []
    pending.append({"target": target, "data": data})
    try:
        with open(WORKLOG_PENDING_FILE, "w") as f:
            json.dump(pending, f, indent=2)
    except Exception as e:
        print(f"Failed to write pending worklog: {e}", file=sys.stderr)

def create_issue(title: str, body: str, repo: str, labels: List[str] | None = None) -> str:
    """Create a GitHub issue and return its URL."""
    token = _get_token()
    if not token:
        return ""

    url = f"{GITHUB_API}/repos/{repo}/issues"
    headers = {"Authorization": f"token {token}"}
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to create issue: {e}", file=sys.stderr)
        return ""
    if resp.status_code >= 300:
        print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
        return ""
    return resp.json().get("html_url", "")

def post_comment(issue_url: str, body: str) -> str:
    """Post a comment on a GitHub issue and return its URL."""
    token = _get_token()
    if not token:
        return ""

    url = f"{issue_url}/comments"
    headers = {"Authorization": f"token {token}"}
    try:
        resp = requests.post(url, headers=headers, json={"body": body}, timeout=10)
    except Exception as e:
        print(f"Failed to post comment: {e}", file=sys.stderr)
        return ""
    if resp.status_code >= 300:
        print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
        return ""
    return resp.json().get("html_url", "")

AGENT_ACTIONS = {
    "create_issue": create_issue,
    "post_comment": post_comment,
}


def _format_worklog(worklog: dict) -> str:
    lines = ["<!-- codex-log -->"]
    if worklog.get("task_name"):
        lines.append(f"**Task:** {worklog['task_name']}")
    if worklog.get("agent_id"):
        lines.append(f"**Agent:** {worklog['agent_id']}")
    if worklog.get("started") or worklog.get("finished"):
        started = worklog.get("started", "")
        finished = worklog.get("finished", "")
        lines.append(f"**Started:** {started}")
        lines.append(f"**Finished:** {finished}")
    if worklog.get("commit"):
        lines.append(f"**Commit:** {worklog['commit']}")

    files = worklog.get("files")
    if files:
        lines.append("\n<details><summary>Files Touched</summary>")
        lines.append("\n| File |")
        lines.append("| --- |")
        for f in files:
            lines.append(f"| {f} |")
        lines.append("</details>")

    decisions = worklog.get("decisions")
    if decisions:
        lines.append("\n<details><summary>Decisions</summary>")
        lines.append(decisions)
        lines.append("</details>")

    if worklog.get("result_summary"):
        lines.append(f"\n**Result:** {worklog['result_summary']}")

    return "\n".join(lines)


def post_worklog_comment(issue_or_pr_url: str, worklog_data: dict) -> str:
    """Create or update a Codex worklog comment on a GitHub issue or PR."""
    token = _get_token()
    if not token:
        _store_pending_worklog(issue_or_pr_url, worklog_data)
        return ""

    comments_url = _comments_url(issue_or_pr_url)
    headers = {"Authorization": f"token {token}"}

    try:
        resp = requests.get(comments_url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Failed to retrieve comments: {e}", file=sys.stderr)
        _store_pending_worklog(issue_or_pr_url, worklog_data)
        return ""
    if resp.status_code >= 300:
        print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
        _store_pending_worklog(issue_or_pr_url, worklog_data)
        return ""

    existing = None
    for c in resp.json():
        if "<!-- codex-log -->" in c.get("body", ""):
            existing = c
            break

    body = _format_worklog(worklog_data)

    if existing:
        url = existing["url"]
        try:
            update = requests.patch(url, headers=headers, json={"body": body}, timeout=10)
        except Exception as e:
            print(f"Failed to update comment: {e}", file=sys.stderr)
            _store_pending_worklog(issue_or_pr_url, worklog_data)
            return ""
        if update.status_code >= 300:
            print(f"GitHub API error {update.status_code}: {update.text}", file=sys.stderr)
            _store_pending_worklog(issue_or_pr_url, worklog_data)
            return ""
        return update.json().get("html_url", "")

    try:
        create = requests.post(comments_url, headers=headers, json={"body": body}, timeout=10)
    except Exception as e:
        print(f"Failed to post comment: {e}", file=sys.stderr)
        _store_pending_worklog(issue_or_pr_url, worklog_data)
        return ""
    if create.status_code >= 300:
        print(f"GitHub API error {create.status_code}: {create.text}", file=sys.stderr)
        _store_pending_worklog(issue_or_pr_url, worklog_data)
        return ""
    return create.json().get("html_url", "")


class CodexAgentLogger:
    """Helper to post worklogs at the end of agent execution."""

    def __init__(self, target_url: str, agent_id: str) -> None:
        self.target_url = target_url
        self.agent_id = agent_id
        self.started: Optional[str] = None

    def start(self) -> None:
        self.started = datetime.utcnow().isoformat()

    def finish(self, worklog: dict) -> None:
        worklog = dict(worklog)
        worklog.setdefault("agent_id", self.agent_id)
        if self.started and "started" not in worklog:
            worklog["started"] = self.started
        worklog.setdefault("finished", datetime.utcnow().isoformat())
        url = post_worklog_comment(self.target_url, worklog)
        if not url:
            print("Worklog comment failed; stored for retry", file=sys.stderr)


