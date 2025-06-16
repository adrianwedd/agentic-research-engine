import time
from pathlib import Path
from typing import Iterable

import yaml

from .internal.issue_logger import format_agent_log, post_markdown_comment


class TaskDaemon:
    """Monitor .codex/queue.yml and post GitHub comments on task events."""

    def __init__(
        self, queue_path: str = ".codex/queue.yml", poll_interval: int = 30
    ) -> None:
        self.queue = Path(queue_path)
        self.poll_interval = poll_interval
        self.seen: set[str] = set()

    def _load_tasks(self) -> Iterable[dict]:
        if not self.queue.exists():
            return []
        with self.queue.open() as f:
            data = yaml.safe_load(f) or []
        return [t for t in data if isinstance(t, dict)]

    def poll_once(self) -> None:
        for task in self._load_tasks():
            tid = task.get("id")
            if not tid or tid in self.seen:
                continue
            issue = task.get("issue_url")
            if issue:
                body = format_agent_log(task.get("title", ""), ["Task started"])
                post_markdown_comment(issue, body)
            self.seen.add(tid)

    def run(self) -> None:
        while True:
            self.poll_once()
            time.sleep(self.poll_interval)


if __name__ == "__main__":
    TaskDaemon().run()
