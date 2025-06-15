import json

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
