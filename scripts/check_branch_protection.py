#!/usr/bin/env python3
"""Verify GitHub branch protection settings.

The script checks that the given branch requires pull requests,
passing status checks, and at least one approving review.
It expects a GitHub personal access token with repo scope.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import requests

API_URL = "https://api.github.com/repos/{repo}/branches/{branch}/protection"


def fetch_rules(repo: str, branch: str, token: str) -> dict[str, Any]:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    url = API_URL.format(repo=repo, branch=branch)
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"failed to fetch protection: {resp.status_code}")
    return resp.json()


def validate_rules(data: dict[str, Any]) -> bool:
    status = data.get("required_status_checks")
    reviews = data.get("required_pull_request_reviews", {})
    return bool(status) and reviews.get("required_approving_review_count", 0) >= 1


def main(branch: str = "main", repo: str | None = None) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = repo or os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GITHUB_TOKEN and GITHUB_REPOSITORY must be set", file=sys.stderr)
        return 1

    try:
        rules = fetch_rules(repo, branch, token)
    except Exception as exc:  # pragma: no cover - network call
        print(str(exc), file=sys.stderr)
        return 1

    if validate_rules(rules):
        print(f"Branch protection for {branch} meets requirements")
        return 0

    print(f"Branch protection for {branch} is insufficient", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(*(sys.argv[1:3])))
