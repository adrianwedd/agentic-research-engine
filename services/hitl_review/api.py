from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from engine.orchestration_engine import OrchestrationEngine

from .queue import InMemoryReviewQueue


class HITLReviewServer:
    """Minimal HTTP API for reviewing paused tasks."""

    def __init__(
        self,
        queue: InMemoryReviewQueue,
        engine: OrchestrationEngine,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.queue = queue
        self.engine = engine
        self.httpd = HTTPServer((host, port), self._handler())

    def _handler(self):
        queue = self.queue
        engine = self.engine

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, status: int, payload: dict) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def do_GET(self) -> None:
                if self.path != "/tasks":
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = {
                    run_id: state.model_dump()
                    for run_id, (state, _) in queue._queue.items()
                }
                self._send_json(200, payload)

            def do_POST(self) -> None:
                parsed = urlparse(self.path)
                parts = parsed.path.strip("/").split("/")
                if len(parts) != 3 or parts[0] != "tasks":
                    self.send_response(404)
                    self.end_headers()
                    return
                run_id, action = parts[1], parts[2]
                if action == "approve":
                    try:
                        state, next_node = queue.pop(run_id)
                    except KeyError:
                        self._send_json(404, {"error": "not found"})
                        return
                    state.update({"status": None})
                    final_state = asyncio.run(
                        engine.run_async(state, thread_id=run_id, start_at=next_node)
                    )
                    self._send_json(200, {"result": final_state.model_dump()})
                elif action == "reject":
                    try:
                        state, _ = queue.pop(run_id)
                    except KeyError:
                        self._send_json(404, {"error": "not found"})
                        return
                    state.update({"status": "REJECTED_BY_HUMAN"})
                    self._send_json(200, state.model_dump())
                else:
                    self.send_response(404)
                    self.end_headers()

        return Handler

    def serve_forever(self) -> None:  # pragma: no cover - manual run
        self.httpd.serve_forever()
