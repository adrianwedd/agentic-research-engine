import io
import json
import os
import sys
from unittest import mock

import pytest
import requests
import yaml

from scripts import issue_logger

pytestmark = pytest.mark.core


def test_create_issue_success():
    with mock.patch.object(issue_logger.requests, "request") as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {
            "html_url": "http://example.com/1",
            "number": 42,
        }
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            result = issue_logger.create_issue("t", "b", "u/r", labels=["l"])
        assert result == {"url": "http://example.com/1", "number": 42}
        m.assert_called_once()
        args, kwargs = m.call_args
        assert args[0] == "post"
        assert args[1] == "https://api.github.com/repos/u/r/issues"
        assert kwargs["headers"]["Authorization"] == "token t"
        assert kwargs["json"]["labels"] == ["l"]


def test_create_issue_no_token(capsys):
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with mock.patch.object(issue_logger.requests, "request") as m:
        result = issue_logger.create_issue("t", "b", "u/r")
    assert result is None
    assert not m.called
    err = capsys.readouterr().err
    assert "GITHUB_TOKEN" in err


def test_post_comment_success():
    with mock.patch.object(issue_logger.requests, "request") as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {"html_url": "http://example.com/c"}
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            url = issue_logger.post_comment("http://example.com/1", "hi")
    assert url == "http://example.com/c"
    m.assert_called_once()
    args, kwargs = m.call_args
    assert args[0] == "post"
    assert args[1] == "http://example.com/1/comments"
    assert kwargs["headers"]["Authorization"] == "token t"


def test_post_worklog_comment_create(tmp_path):
    wl_file = tmp_path / "pending.json"
    with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}), mock.patch.object(
        issue_logger, "WORKLOG_PENDING_FILE", str(wl_file)
    ), mock.patch.object(issue_logger.requests, "request") as req:
        g_resp = mock.Mock(status_code=200)
        g_resp.json.return_value = []
        p_resp = mock.Mock(status_code=201)
        p_resp.json.return_value = {"html_url": "http://example.com/c"}
        req.side_effect = [g_resp, p_resp]
        url = issue_logger.post_worklog_comment(
            "http://example.com/issues/1", {"task_name": "t", "agent_id": "a"}
        )
    assert url == "http://example.com/c"
    assert req.call_count == 2
    call1, call2 = req.call_args_list
    assert call1.args[0] == "get"
    assert call2.args[0] == "post"
    assert call2.args[1] == "http://example.com/issues/1/comments"
    assert call2.kwargs["headers"]["Authorization"] == "token t"


def test_post_worklog_comment_update():
    existing = {
        "body": "x <!-- codex-log -->",
        "url": "http://example.com/comments/1",
        "html_url": "http://example.com/c1",
    }
    with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}), mock.patch.object(
        issue_logger.requests, "request"
    ) as req:
        g_resp = mock.Mock(status_code=200)
        g_resp.json.return_value = [existing]
        patch_resp = mock.Mock(status_code=200)
        patch_resp.json.return_value = {"html_url": "http://example.com/c1"}
        req.side_effect = [g_resp, patch_resp]
        url = issue_logger.post_worklog_comment(
            "http://example.com/issues/1", {"task_name": "t", "agent_id": "a"}
        )
    assert url == "http://example.com/c1"
    assert req.call_count == 2
    assert req.call_args_list[1].args[0] == "patch"
    assert req.call_args_list[1].args[1] == "http://example.com/comments/1"


def test_post_worklog_comment_pr_url():
    with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}), mock.patch.object(
        issue_logger.requests, "request"
    ) as req:
        g_resp = mock.Mock(status_code=200)
        g_resp.json.return_value = []
        p_resp = mock.Mock(status_code=201)
        p_resp.json.return_value = {"html_url": "http://example.com/c"}
        req.side_effect = [g_resp, p_resp]
        issue_logger.post_worklog_comment(
            "http://example.com/pulls/2", {"task_name": "t", "agent_id": "a"}
        )
    req.assert_any_call(
        "get",
        "http://example.com/issues/2/comments",
        headers={"Authorization": "token t"},
        timeout=10,
    )


def test_post_worklog_comment_no_token(tmp_path):
    wl_file = tmp_path / "pending.json"
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with mock.patch.object(issue_logger, "WORKLOG_PENDING_FILE", str(wl_file)):
        issue_logger.post_worklog_comment(
            "http://example.com/issues/1", {"task_name": "t"}
        )
    assert wl_file.exists()


def test_request_with_retry_recovers(monkeypatch):
    calls = []

    def fake_request(method, url, timeout=10, **kwargs):
        if not calls:
            calls.append(True)
            raise requests.RequestException("boom")
        resp = mock.Mock(status_code=200)
        return resp

    monkeypatch.setattr(issue_logger.requests, "request", fake_request)
    monkeypatch.setattr(issue_logger.time, "sleep", lambda s: None)

    resp = issue_logger._request_with_retry("get", "http://x", retries=2)
    assert resp.status_code == 200


def test_store_pending_worklog_atomic(tmp_path):
    wl_file = tmp_path / "pending.json"
    with mock.patch.object(issue_logger, "WORKLOG_PENDING_FILE", str(wl_file)):
        issue_logger._store_pending_worklog("t1", {"a": 1})
        issue_logger._store_pending_worklog("t2", {"b": 2})
    with open(wl_file) as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["target"] == "t1"
    assert data[1]["target"] == "t2"


def test_read_body_sources(tmp_path, monkeypatch):
    p = tmp_path / "b.txt"
    p.write_text("hello")
    assert issue_logger._read_body(str(p)) == "hello"
    monkeypatch.setattr(sys, "stdin", io.StringIO("bye"))
    assert issue_logger._read_body("-") == "bye"


def test_cli_worklog(monkeypatch, tmp_path):
    wl_file = tmp_path / "wl.yml"
    data = {"task_name": "t"}
    wl_file.write_text(yaml.safe_dump(data))

    called = {}

    def fake(url, d):
        called["url"] = url
        called["data"] = d

    monkeypatch.setattr(issue_logger, "post_worklog_comment", fake)

    issue_logger.main(
        [
            "worklog",
            "--repo",
            "u/r",
            "--issue",
            "2",
            "--worklog",
            str(wl_file),
        ]
    )

    assert called["url"] == f"{issue_logger.GITHUB_API}/repos/u/r/issues/2"
    assert called["data"] == data
