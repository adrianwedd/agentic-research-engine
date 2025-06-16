import os
from unittest import mock

import yaml

from scripts import codex_notary


def test_create_issue_updates_queue(tmp_path):
    queue = tmp_path / "queue.yml"
    data = [
        {"id": "CR-1", "title": "Test", "phase": "Automation", "epic": "Codex Workflow"}
    ]
    queue.write_text(yaml.safe_dump(data))

    called = {}

    def fake_create_issue(title, body, repo, labels=None):
        called["title"] = title
        called["labels"] = labels
        return {"url": "https://api.github.com/repos/u/r/issues/42", "number": 42}

    with mock.patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "u/r", "GITHUB_TOKEN": "t"}
    ), mock.patch.object(codex_notary.issue_logger, "create_issue", fake_create_issue):
        exitcode = codex_notary.main([str(queue)])

    assert exitcode == 0
    updated = yaml.safe_load(queue.read_text())
    assert updated[0]["issue_id"] == 42
    assert called["title"].startswith("CR-1")
    assert "phase:Automation" in called["labels"]
