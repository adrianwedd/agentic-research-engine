import threading

import pytest
import requests
import yaml

from agentic_index_cli.task_suggestions import load_suggested_tasks
from services.task_suggestions import TaskSuggestionServer

pytestmark = pytest.mark.core


def test_load_suggested_tasks(tmp_path):
    queue = tmp_path / "queue.yml"
    queue.write_text(
        yaml.safe_dump(
            [
                {"id": "A", "title": "done", "status": "done"},
                {"id": "B", "title": "todo"},
                {"id": "C", "title": "open", "status": "open"},
            ]
        )
    )
    tasks = load_suggested_tasks(queue)
    assert tasks == [
        {"id": "B", "title": "todo"},
        {"id": "C", "title": "open"},
    ]


def test_task_suggestion_api(tmp_path):
    queue = tmp_path / "queue.yml"
    queue.write_text(yaml.safe_dump([{"id": "T1", "title": "demo"}]))

    server = TaskSuggestionServer(str(queue), host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.httpd.server_port}/suggested_tasks"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200
        assert resp.json() == [{"id": "T1", "title": "demo"}]
    finally:
        server.httpd.shutdown()
        thread.join()
