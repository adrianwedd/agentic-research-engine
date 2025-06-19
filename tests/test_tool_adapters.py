from unittest import mock

from tools import adapters


def test_execute_dispatches():
    call = adapters.ToolCall(name="web.search", args={"query": "ai"})
    fake = mock.Mock(return_value=[{"url": "x"}])
    adapters._REGISTRY["web.search"] = fake
    result = adapters.execute(call)
    fake.assert_called_once_with(query="ai")
    assert result == [{"url": "x"}]
