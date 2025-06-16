import argparse
import datetime
import fcntl
import json
import os
import sys
import tempfile
import time
from typing import List, Optional

import requests
import yaml

GITHUB_API = "https://api.github.com"
WORKLOG_PENDING_FILE = os.path.join("state", "worklog_pending.json")


def _get_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "Error: GITHUB_TOKEN not set. Set the environment variable to enable issue logging.",
            file=sys.stderr,
        )
        return None
    return token


def _comments_url(issue_or_pr_url: str) -> str:
    if "/pulls/" in issue_or_pr_url:
        issue_or_pr_url = issue_or_pr_url.replace("/pulls/", "/issues/")
    return f"{issue_or_pr_url}/comments"


def _request_with_retry(method: str, url: str, *, retries: int = 3, **kwargs):
    """Perform an HTTP request with exponential backoff."""
    backoff = 1
    for attempt in range(retries):
        try:
            resp = requests.request(method, url, timeout=10, **kwargs)
        except requests.RequestException as e:
            err: Exception | None = e
        else:
            if resp.status_code in {429, 500, 502, 503, 504} or (
                resp.status_code == 403 and "rate limit" in resp.text.lower()
            ):
                err = RuntimeError(f"HTTP {resp.status_code}")
            else:
                return resp
        if attempt < retries - 1:
            time.sleep(backoff)
            backoff *= 2
        else:
            print(
                f"{method.upper()} {url} failed after {retries} attempts: {err}",
                file=sys.stderr,
            )
            return None


def _store_pending_worklog(target: str, data: dict) -> None:
    os.makedirs(os.path.dirname(WORKLOG_PENDING_FILE), exist_ok=True)
    lock_path = f"{WORKLOG_PENDING_FILE}.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pending = []
        if os.path.exists(WORKLOG_PENDING_FILE):
            try:
                with open(WORKLOG_PENDING_FILE) as f:
                    pending = json.load(f) or []
            except Exception:
                pending = []
        pending.append({"target": target, "data": data})
        try:
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(WORKLOG_PENDING_FILE))
            with os.fdopen(fd, "w") as f:
                json.dump(pending, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, WORKLOG_PENDING_FILE)
        except Exception as e:
            print(f"Failed to write pending worklog: {e}", file=sys.stderr)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def create_issue(
    title: str, body: str, repo: str, labels: List[str] | None = None
) -> str:
    """Create a GitHub issue and return its URL."""
    token = _get_token()
    if not token:
        return ""

    url = f"{GITHUB_API}/repos/{repo}/issues"
    headers = {"Authorization": f"token {token}"}
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    resp = _request_with_retry("post", url, headers=headers, json=payload)
    if not resp:
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
    resp = _request_with_retry("post", url, headers=headers, json={"body": body})
    if not resp:
        return ""
    if resp.status_code >= 300:
        print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
        return ""
    return resp.json().get("html_url", "")


AGENT_ACTIONS = {
    "create_issue": create_issue,
    "post_comment": post_comment,
}


def _read_body(arg: str | None) -> str:
    """Return body text from stdin, file, or direct string."""
    if not arg:
        return ""
    if arg == "-":
        return sys.stdin.read()
    if os.path.exists(arg):
        with open(arg) as f:
            return f.read()
    return arg


def _load_worklog(path: str) -> dict:
    """Load a worklog mapping from JSON or YAML file."""
    with open(path) as f:
        text = f.read()
    try:
        return json.loads(text)
    except Exception:
        return yaml.safe_load(text)


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

    resp = _request_with_retry("get", comments_url, headers=headers)
    if not resp:
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
        update = _request_with_retry("patch", url, headers=headers, json={"body": body})
        if not update:
            _store_pending_worklog(issue_or_pr_url, worklog_data)
            return ""
        if update.status_code >= 300:
            print(
                f"GitHub API error {update.status_code}: {update.text}",
                file=sys.stderr,
            )
            _store_pending_worklog(issue_or_pr_url, worklog_data)
            return ""
        return update.json().get("html_url", "")

    create = _request_with_retry(
        "post", comments_url, headers=headers, json={"body": body}
    )
    if not create:
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
        self.started = datetime.datetime.now(datetime.UTC).isoformat()

    def finish(self, worklog: dict) -> None:
        worklog = dict(worklog)
        worklog.setdefault("agent_id", self.agent_id)
        if self.started and "started" not in worklog:
            worklog["started"] = self.started
        worklog.setdefault("finished", datetime.datetime.now(datetime.UTC).isoformat())
        url = post_worklog_comment(self.target_url, worklog)
        if not url:
            print("Worklog comment failed; stored for retry", file=sys.stderr)


def _resolve_target_url(
    repo: str | None, issue: int | None, pr: int | None, url: str | None
) -> str:
    if url:
        return url
    if repo and issue:
        return f"{GITHUB_API}/repos/{repo}/issues/{issue}"
    if repo and pr:
        return f"{GITHUB_API}/repos/{repo}/pulls/{pr}"
    raise SystemExit("Target URL not provided")


def main(argv: Optional[List[str]] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Codex issue logger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ci = sub.add_parser("create")
    ci.add_argument("--repo", required=True)
    ci.add_argument("--title", required=True)
    ci.add_argument("--body")
    ci.add_argument("--labels", nargs="*")

    cc = sub.add_parser("comment")
    cc.add_argument("--url", required=True)
    cc.add_argument("--body")

    wl = sub.add_parser("worklog")
    wl.add_argument("--repo")
    wl.add_argument("--issue", type=int)
    wl.add_argument("--pr", type=int)
    wl.add_argument("--url")
    wl.add_argument("--worklog", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "create":
        body = _read_body(args.body)
        create_issue(args.title, body, args.repo, args.labels)
    elif args.cmd == "comment":
        body = _read_body(args.body)
        post_comment(args.url, body)
    else:  # worklog
        target = _resolve_target_url(args.repo, args.issue, args.pr, args.url)
        data = _load_worklog(args.worklog)
        post_worklog_comment(target, data)


if __name__ == "__main__":
    main()
