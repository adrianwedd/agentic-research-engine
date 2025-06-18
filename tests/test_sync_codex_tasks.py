import os
from unittest import mock

import pytest

from scripts import sync_codex_tasks

pytestmark = pytest.mark.core


def test_sync_detects_mismatch(tmp_path):
    queue = tmp_path / "queue.yml"
    queue.write_text("- id: CR-1\n")

    def fake_get(url, headers=None, timeout=10):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = [
            {"title": "CR-2", "labels": [{"name": "Codex Task"}]},
        ]
        resp.links = {}
        return resp

    with mock.patch.object(
        sync_codex_tasks, "GITHUB_API", "http://api"
    ), mock.patch.object(sync_codex_tasks.requests, "get", fake_get), mock.patch.dict(
        os.environ, {"GITHUB_REPOSITORY": "u/r", "GITHUB_TOKEN": "t"}
    ):
        with mock.patch("builtins.open", mock.mock_open(read_data=queue.read_text())):
            exitcode = sync_codex_tasks.main()
    assert exitcode == 1


def test_sync_uses_git_repo(tmp_path):
    queue = tmp_path / "queue.yml"
    queue.write_text("- id: CR-1\n")

    def fake_get(url, headers=None, timeout=10):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = [
            {"title": "CR-2", "labels": [{"name": "Codex Task"}]},
        ]
        resp.links = {}
        return resp

    with mock.patch.object(
        sync_codex_tasks.requests, "get", fake_get
    ), mock.patch.object(
        sync_codex_tasks, "guess_repo_from_git", return_value="u/r"
    ), mock.patch.dict(
        os.environ, {}, clear=True
    ):
        with mock.patch("builtins.open", mock.mock_open(read_data=queue.read_text())):
            exitcode = sync_codex_tasks.main()
    assert exitcode == 1


def test_sync_requires_repo_when_unknown(capsys):
    with mock.patch.object(
        sync_codex_tasks, "guess_repo_from_git", return_value=None
    ), mock.patch.dict(os.environ, {}, clear=True):

        exitcode = sync_codex_tasks.main()
    captured = capsys.readouterr()
    assert exitcode == 1
    assert "GITHUB_REPOSITORY" in captured.err
