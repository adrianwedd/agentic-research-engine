import os
from unittest import mock

from scripts import issue_logger


def test_create_issue_success():
    with mock.patch.object(issue_logger.requests, "post") as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {"html_url": "http://example.com/1"}
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            url = issue_logger.create_issue("t", "b", "u/r", labels=["l"])
        assert url == "http://example.com/1"
        m.assert_called_once()
        args, kwargs = m.call_args
        assert args[0] == "https://api.github.com/repos/u/r/issues"
        assert kwargs["headers"]["Authorization"] == "token t"
        assert kwargs["json"]["labels"] == ["l"]


def test_create_issue_no_token(capsys):
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with mock.patch.object(issue_logger.requests, "post") as m:
        url = issue_logger.create_issue("t", "b", "u/r")
    assert url == ""
    assert not m.called
    err = capsys.readouterr().err
    assert "GITHUB_TOKEN" in err


def test_post_comment_success():
    with mock.patch.object(issue_logger.requests, "post") as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {"html_url": "http://example.com/c"}
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            url = issue_logger.post_comment("http://example.com/1", "hi")
    assert url == "http://example.com/c"
    m.assert_called_once()
    args, kwargs = m.call_args
    assert args[0] == "http://example.com/1/comments"
    assert kwargs["headers"]["Authorization"] == "token t"


def test_post_worklog_comment_create(tmp_path):
    wl_file = tmp_path / "pending.json"
    with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}), mock.patch.object(
        issue_logger, "WORKLOG_PENDING_FILE", str(wl_file)
    ), mock.patch.object(issue_logger.requests, "get") as g, mock.patch.object(
        issue_logger.requests, "post"
    ) as p:
        g.return_value.status_code = 200
        g.return_value.json.return_value = []
        p.return_value.status_code = 201
        p.return_value.json.return_value = {"html_url": "http://example.com/c"}
        url = issue_logger.post_worklog_comment(
            "http://example.com/issues/1", {"task_name": "t", "agent_id": "a"}
        )
    assert url == "http://example.com/c"
    g.assert_called_once()
    p.assert_called_once()
    args, kwargs = p.call_args
    assert args[0] == "http://example.com/issues/1/comments"
    assert kwargs["headers"]["Authorization"] == "token t"


def test_post_worklog_comment_update():
    existing = {
        "body": "x <!-- codex-log -->",
        "url": "http://example.com/comments/1",
        "html_url": "http://example.com/c1",
    }
    with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}), mock.patch.object(
        issue_logger.requests, "get"
    ) as g, mock.patch.object(issue_logger.requests, "patch") as patch_req:
        g.return_value.status_code = 200
        g.return_value.json.return_value = [existing]
        patch_req.return_value.status_code = 200
        patch_req.return_value.json.return_value = {"html_url": "http://example.com/c1"}
        url = issue_logger.post_worklog_comment(
            "http://example.com/issues/1", {"task_name": "t", "agent_id": "a"}
        )
    assert url == "http://example.com/c1"
    g.assert_called_once()
    patch_req.assert_called_once_with(
        "http://example.com/comments/1",
        headers={"Authorization": "token t"},
        json=mock.ANY,
        timeout=10,
    )


def test_post_worklog_comment_pr_url():
    with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}), mock.patch.object(
        issue_logger.requests, "get"
    ) as g, mock.patch.object(issue_logger.requests, "post") as p:
        g.return_value.status_code = 200
        g.return_value.json.return_value = []
        p.return_value.status_code = 201
        p.return_value.json.return_value = {"html_url": "http://example.com/c"}
        issue_logger.post_worklog_comment(
            "http://example.com/pulls/2", {"task_name": "t", "agent_id": "a"}
        )
    g.assert_called_once_with(
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
