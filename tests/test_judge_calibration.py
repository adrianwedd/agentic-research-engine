import json
from pathlib import Path

from pipelines.judge.pipeline import JudgePipeline


def cohen_kappa(rater_a, rater_b):
    assert len(rater_a) == len(rater_b)
    categories = sorted(set(rater_a) | set(rater_b))
    index = {cat: i for i, cat in enumerate(categories)}
    n = len(categories)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    for a, b in zip(rater_a, rater_b):
        matrix[index[a]][index[b]] += 1
    total = len(rater_a)
    po = sum(matrix[i][i] for i in range(n)) / total
    row_marginals = [sum(row) / total for row in matrix]
    col_marginals = [sum(matrix[i][j] for i in range(n)) / total for j in range(n)]
    pe = sum(r * c for r, c in zip(row_marginals, col_marginals))
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def test_judge_calibration_mean_kappa_above_threshold(tmp_path):
    dataset_file = Path("data/golden_judge_dataset/golden_dataset.json")
    dataset = json.loads(dataset_file.read_text(encoding="utf-8"))
    criteria = [
        "factual_accuracy",
        "completeness",
        "source_quality",
        "coherence",
    ]

    counter = {"index": 0}

    def fake_llm(_prompt: str) -> str:
        record = dataset[counter["index"]]
        counter["index"] += 1
        return json.dumps(record["scores"])

    pipeline = JudgePipeline(fake_llm, db_path=str(tmp_path / "results.db"))

    llm_scores = {c: [] for c in criteria}
    human_scores = {c: [] for c in criteria}
    for record in dataset:
        result = pipeline.evaluate(record["report"], [])
        for crit in criteria:
            human_scores[crit].append(round(record["scores"][crit]["score"], 1))
            llm_scores[crit].append(round(result[crit]["score"], 1))

    pipeline.close()

    kappas = {}
    for crit in criteria:
        kappas[crit] = cohen_kappa(human_scores[crit], llm_scores[crit])
    mean_kappa = sum(kappas.values()) / len(kappas)

    report = {"kappas": kappas, "mean_kappa": mean_kappa}
    report_path = tmp_path / "calibration_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    assert mean_kappa >= 0.7, f"Mean kappa below threshold: {mean_kappa}"
