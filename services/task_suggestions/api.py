from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List

from agentic_index_cli.task_suggestions import load_suggested_tasks


class TaskSuggestionServer:
    """Minimal HTTP API exposing suggested Codex tasks."""

    def __init__(
        self,
        queue_path: str = ".codex/queue.yml",
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.queue_path = queue_path
        self.httpd = HTTPServer((host, port), self._handler())

    def _handler(self):
        queue_path = self.queue_path

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, status: int, payload: List[Dict[str, str]]) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def do_GET(self) -> None:
                if self.path != "/suggested_tasks":
                    self.send_response(404)
                    self.end_headers()
                    return
                tasks = load_suggested_tasks(queue_path)
                self._send_json(200, tasks)

        return Handler

    def serve_forever(self) -> None:  # pragma: no cover - manual run
        self.httpd.serve_forever()
