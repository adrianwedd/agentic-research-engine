import json
import time

from tests.benchmarks.integration_harness import IntegrationTestHarness

DATASET = "benchmarks/browsecomp/dataset_v1.json"


def test_harness_with_perfect_agent():
    with open(DATASET, "r", encoding="utf-8") as f:
        cases = json.load(f)

    answer_lookup = {c["question"]: c["answer"] for c in cases}

    def agent(question: str) -> dict:
        return {"answer": answer_lookup.get(question, "")}

    harness = IntegrationTestHarness(DATASET, timeout=1)
    report = harness.run(agent)
    assert report["total_cases"] == len(cases)
    assert report["passed"] == len(cases)
    assert report["pass_rate"] == 1.0
    assert report["average_time"] >= 0


def test_harness_timeout_does_not_abort(tmp_path, monkeypatch):
    data = [
        {"question": "fast", "answer": "ok"},
        {"question": "slow", "answer": "delay"},
    ]
    dataset = tmp_path / "data.json"
    dataset.write_text(json.dumps(data))

    def agent(question: str) -> dict:
        if question == "slow":
            time.sleep(0.2)
            return {"answer": "delay"}
        return {"answer": "ok"}

    monkeypatch.setenv("HARNESS_TIMEOUT", "0.05")
    monkeypatch.setenv("HARNESS_RETRIES", "1")

    harness = IntegrationTestHarness(str(dataset))
    report = harness.run(agent)
    assert report["total_cases"] == 2
    assert report["passed"] == 1
    assert any(r["timed_out"] for r in report["results"] if r["question"] == "slow")
