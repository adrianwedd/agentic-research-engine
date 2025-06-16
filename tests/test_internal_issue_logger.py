import os
from unittest import mock

import pytest

from agentic_index_cli.internal import issue_logger

pytestmark = pytest.mark.core


def test_format_agent_log():
    body = issue_logger.format_agent_log("CR text", ["a", "b"])
    assert "CR text" in body
    assert "a" in body
    assert "b" in body


def test_post_markdown_comment_success():
    with mock.patch.object(issue_logger.requests, "post") as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {"html_url": "http://x"}
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            url = issue_logger.post_markdown_comment("http://example.com/1", "hi")
        assert url == "http://x"
        m.assert_called_once()
        args, kwargs = m.call_args
        assert args[0] == "http://example.com/1/comments"
        assert kwargs["headers"]["Authorization"] == "token t"


def test_post_markdown_comment_no_token():
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    with mock.patch.object(issue_logger.requests, "post") as m:
        url = issue_logger.post_markdown_comment("http://example.com/1", "hi")
    assert url == ""
    assert not m.called
