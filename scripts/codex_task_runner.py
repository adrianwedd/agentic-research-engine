#!/usr/bin/env python3
"""Simple Codex task queue runner."""
import time
from pathlib import Path

import yaml


class Task:
    """Represents a queue task."""

    def __init__(self, spec: dict):
        self.id = spec["id"]
        self.priority = spec.get("priority", "normal")
        self.retry_policy = spec.get(
            "retry_policy", {"max_retries": 1, "backoff_seconds": 0}
        )
        self.timeout = spec.get("timeout")
        self.attempts = 0

    def execute(self, vars_: dict) -> bool:
        """Execute the task. Replace with real agent call."""
        print(f"\u25B6\uFE0F  Executing Task {self.id} (priority={self.priority})")
        time.sleep(1)
        return True

    def on_fail(self) -> bool:
        """Handle a failed attempt; return True if we should retry."""
        self.attempts += 1
        if self.attempts <= self.retry_policy.get("max_retries", 0):
            backoff = self.retry_policy.get("backoff_seconds", 0)
            print(f"\u26A0\uFE0F  Retry {self.id} in {backoff}s (attempt {self.attempts})")
            time.sleep(backoff)
            return True
        return False


class QueueManager:
    """Loads queue spec and runs tasks sequentially."""

    def __init__(self, path: str | Path):
        data = yaml.safe_load(Path(path).read_text())
        self.queue = data.get("queue", [])
        self.vars = data.get("vars", {})

    def run(self) -> None:
        for spec in self.queue:
            task = Task(spec)
            success = task.execute(self.vars)
            while not success and task.on_fail():
                success = task.execute(self.vars)
            if not success:
                print(f"\u274C  Task {task.id} failed permanently.")
                break
            print(f"\u2705  Task {task.id} completed.")


def main() -> None:
    QueueManager(".codex/queue.yml").run()


if __name__ == "__main__":
    main()
