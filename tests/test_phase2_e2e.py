import asyncio
import json
from pathlib import Path
from threading import Thread

from agents.memory_manager import MemoryManagerAgent
from agents.supervisor import SupervisorAgent
from engine.orchestration_engine import GraphState, create_orchestration_engine
from engine.routing import make_cosc_router
from services.ltm_service import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.api import LTMService, LTMServiceServer


def _start_server():
    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"
    return server, endpoint


def test_learn_and_recall_cycle():
    server, endpoint = _start_server()
    mm = MemoryManagerAgent(endpoint=endpoint)

    sup_first = SupervisorAgent(ltm_endpoint=endpoint, use_plan_templates=False)
    state = sup_first.analyze_query("Transformer vs LSTM")
    mm(state)
    stored = server.service.retrieve("episodic", {"query": "Transformer vs LSTM"})
    assert stored, "memory not consolidated"
    first_nodes = len(state.data["plan"]["graph"]["nodes"])

    sup_default = SupervisorAgent(ltm_endpoint=endpoint, use_plan_templates=False)
    baseline = sup_default.plan_research_task("Transformer vs LSTM vs CNN")
    baseline_nodes = len(baseline["graph"]["nodes"])

    sup_recall = SupervisorAgent(
        ltm_endpoint=endpoint, use_plan_templates=True, retrieval_limit=1
    )
    recalled = sup_recall.plan_research_task("Transformer vs LSTM vs CNN")
    recalled_nodes = len(recalled["graph"]["nodes"])

    assert recalled["context"], "episodic memory should be recalled"
    assert recalled_nodes == first_nodes
    assert recalled_nodes < baseline_nodes
    server.httpd.shutdown()


def test_critique_and_correct_cycle():
    engine = create_orchestration_engine()
    calls = {"n": 0}

    def researcher(state: GraphState, _sp: dict) -> GraphState:
        if calls["n"] == 0:
            state.update({"report": "Paris is the capital of Germany"})
        else:
            state.update({"report": "Paris is the capital of France"})
        calls["n"] += 1
        return state

    def evaluator(state: GraphState, _sp: dict) -> GraphState:
        if "Germany" in state.data.get("report", ""):
            state.evaluator_feedback = {"overall_score": 0.0}
        else:
            state.evaluator_feedback = {"overall_score": 1.0}
        return state

    engine.add_node("Researcher", researcher)
    engine.add_node("Evaluator", evaluator)
    engine.add_node("Complete", lambda s, sp: s)
    engine.add_edge("Researcher", "Evaluator")
    router = make_cosc_router(
        retry_node="Researcher",
        pass_node="Complete",
        max_retries=2,
        score_threshold=0.5,
    )
    engine.add_router("Evaluator", router)

    result = asyncio.run(engine.run_async(GraphState()))
    assert result.data["report"] == "Paris is the capital of France"
    assert calls["n"] == 2


def test_critique_loop_terminates_after_max_retries():
    engine = create_orchestration_engine()

    def researcher(state: GraphState, _sp: dict) -> GraphState:
        state.update({"report": "error"})
        return state

    def evaluator(state: GraphState, _sp: dict) -> GraphState:
        state.evaluator_feedback = {"overall_score": 0.0}
        return state

    engine.add_node("Researcher", researcher)
    engine.add_node("Evaluator", evaluator)
    engine.add_node("Abort", lambda s, sp: s)
    engine.add_edge("Researcher", "Evaluator")
    router = make_cosc_router(
        retry_node="Researcher",
        pass_node="Abort",
        max_retries=3,
        score_threshold=0.5,
        fail_node="Abort",
    )
    engine.add_router("Evaluator", router)

    result = asyncio.run(engine.run_async(GraphState()))
    assert result.retry_count == 3


def test_judge_pipeline_calibration(tmp_path):
    from pipelines.judge.pipeline import JudgePipeline
    from tests.test_judge_calibration import cohen_kappa

    dataset = json.loads(
        Path("data/golden_judge_dataset/golden_dataset.json").read_text(
            encoding="utf-8"
        )
    )[:10]
    counter = {"i": 0}

    def fake_llm(_prompt: str) -> str:
        rec = dataset[counter["i"]]
        counter["i"] += 1
        return json.dumps(rec["scores"])

    pipeline = JudgePipeline(fake_llm, db_path=str(tmp_path / "results.db"))

    llm_scores = {
        c: []
        for c in ["factual_accuracy", "completeness", "source_quality", "coherence"]
    }
    human_scores = {c: [] for c in llm_scores}

    for record in dataset:
        result = pipeline.evaluate(record["report"], [])
        for crit in llm_scores:
            human_scores[crit].append(round(record["scores"][crit]["score"], 1))
            llm_scores[crit].append(round(result[crit]["score"], 1))

    pipeline.close()

    kappas = {c: cohen_kappa(human_scores[c], llm_scores[c]) for c in llm_scores}
    mean_kappa = sum(kappas.values()) / len(kappas)
    assert mean_kappa >= 0.7
