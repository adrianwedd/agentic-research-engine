import json
from unittest import mock

from scripts import codex_archivist


def test_archivist_posts_worklog(tmp_path):
    wl = tmp_path / "wl.json"
    wl.write_text(json.dumps({"task_name": "t"}))

    called = {}

    def fake_post(url, data):
        called["url"] = url
        called["data"] = data
        return "http://example.com/c1"

    with mock.patch.object(
        codex_archivist.issue_logger, "post_worklog_comment", fake_post
    ):
        exitcode = codex_archivist.main(
            ["--repo", "u/r", "--issue", "42", "--worklog", str(wl)]
        )

    assert exitcode == 0
    assert called["url"].endswith("/repos/u/r/issues/42")
    assert called["data"]["task_name"] == "t"
