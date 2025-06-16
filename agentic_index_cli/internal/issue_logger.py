import os
from typing import Iterable

import requests

GITHUB_API = "https://api.github.com"


def format_agent_log(cr_text: str, log_lines: Iterable[str]) -> str:
    lines = ["<!-- codex-log -->"]
    if cr_text:
        lines.append("<details><summary>Change Request</summary>")
        lines.append(cr_text)
        lines.append("</details>")
    lines.append("<details><summary>Worklog</summary>")
    lines.append("```text")
    for line in log_lines:
        lines.append(line)
    lines.append("```")
    lines.append("</details>")
    return "\n".join(lines)


def post_markdown_comment(issue_url: str, body: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return ""
    headers = {"Authorization": f"token {token}"}
    resp = requests.post(
        f"{issue_url}/comments", headers=headers, json={"body": body}, timeout=10
    )
    if resp.status_code >= 300:
        return ""
    return resp.json().get("html_url", "")
