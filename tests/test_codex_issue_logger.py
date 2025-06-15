import os
from unittest import mock

from scripts import issue_logger


def test_create_issue_success():
    with mock.patch.object(issue_logger.requests, 'post') as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {'html_url': 'http://example.com/1'}
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            url = issue_logger.create_issue('t', 'b', 'u/r', labels=['l'])
        assert url == 'http://example.com/1'
        m.assert_called_once()
        args, kwargs = m.call_args
        assert args[0] == 'https://api.github.com/repos/u/r/issues'
        assert kwargs['headers']['Authorization'] == 'token t'
        assert kwargs['json']['labels'] == ['l']


def test_create_issue_no_token(capsys):
    if 'GITHUB_TOKEN' in os.environ:
        del os.environ['GITHUB_TOKEN']
    with mock.patch.object(issue_logger.requests, 'post') as m:
        url = issue_logger.create_issue('t', 'b', 'u/r')
    assert url == ''
    assert not m.called
    err = capsys.readouterr().err
    assert 'GITHUB_TOKEN' in err


def test_post_comment_success():
    with mock.patch.object(issue_logger.requests, 'post') as m:
        m.return_value.status_code = 201
        m.return_value.json.return_value = {'html_url': 'http://example.com/c'}
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "t"}):
            url = issue_logger.post_comment('http://example.com/1', 'hi')
    assert url == 'http://example.com/c'
    m.assert_called_once()
    args, kwargs = m.call_args
    assert args[0] == 'http://example.com/1/comments'
    assert kwargs['headers']['Authorization'] == 'token t'

