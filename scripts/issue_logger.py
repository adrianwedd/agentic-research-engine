import os
import sys
from typing import List

import requests

GITHUB_API = "https://api.github.com"

def _get_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN not set. Set the environment variable to enable issue logging.", file=sys.stderr)
        return None
    return token

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

