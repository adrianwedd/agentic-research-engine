import asyncio

import pytest

from agents.manager import ManagerAgent

pytestmark = pytest.mark.core


def test_manager_agent_delegates_tasks_sequentially():
    calls = []

    def web_worker(messages, state, scratchpad):
        calls.append("web")
        return "web done"

    def code_worker(messages, state, scratchpad):
        calls.append("code")
        return {"content": "code done"}

    manager = ManagerAgent(web_worker, code_worker)
    result = asyncio.run(manager.run_async("Need web research and code analysis"))

    assert calls == ["web", "code"]
    senders = [m["sender"] for m in result.messages]
    assert senders[0] == "Manager"
    assert "WebResearcher" in senders and "CodeResearcher" in senders
