import asyncio
from threading import Thread

import pytest

from agents.evaluator import EvaluatorAgent
from agents.memory_manager import MemoryManagerAgent
from agents.supervisor import SupervisorAgent
from engine.collaboration.group_chat import GroupChatManager
from engine.orchestration_engine import GraphState
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer

pytestmark = pytest.mark.core


def _start_server():
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_mast_step_repetition():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint)

    sup_first = SupervisorAgent(ltm_endpoint=endpoint, use_plan_templates=False)
    state = sup_first.analyze_query("Transformer vs LSTM")
    mm(state, {})

    sup_base = SupervisorAgent(ltm_endpoint=endpoint, use_plan_templates=False)
    baseline = sup_base.plan_research_task("Transformer vs LSTM vs CNN")
    baseline_len = len(baseline["graph"]["nodes"])

    sup_recall = SupervisorAgent(
        ltm_endpoint=endpoint, use_plan_templates=True, retrieval_limit=1
    )
    recalled = sup_recall.plan_research_task("Transformer vs LSTM vs CNN")
    recalled_len = len(recalled["graph"]["nodes"])

    assert recalled["context"], "episodic memory should be recalled"
    assert recalled_len < baseline_len
    server.httpd.shutdown()


def test_mast_information_withholding():
    def agent_a(messages, state, scratch):
        return {"content": "42", "type": "message", "recipient": "B"}

    def agent_b(messages, state, scratch):
        if messages:
            state.update({"answer": messages[0]["content"]})
        return {"content": "FINISH", "type": "finish"}

    manager = GroupChatManager({"A": agent_a, "B": agent_b}, max_turns=2)
    state = GraphState()
    result = asyncio.run(manager.run(state))

    assert result.data.get("answer") == "42"


def test_mast_incorrect_verification():
    agent = EvaluatorAgent()
    summary = "Paris is the capital of Germany."
    sources = ["Paris is the capital of France."]
    result = agent.verify_factual_accuracy(summary, sources)
    assert "Paris is the capital of Germany." in result["unsupported_facts"]
