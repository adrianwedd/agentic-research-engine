import json
from pathlib import Path
import sqlite3

from pipelines.judge.pipeline import JudgePipeline

FIXTURES = Path(__file__).parent / "fixtures"


def _load_cases():
    cases = []
    for path in sorted(FIXTURES.glob("case*.json")):
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    return cases


def test_judge_pipeline_contracts(tmp_path):
    cases = _load_cases()
    idx = {"i": 0}

    def fake_llm(_prompt: str) -> str:
        data = cases[idx["i"]]["scores"]
        idx["i"] += 1
        return json.dumps(data)

    db_file = tmp_path / "results.db"
    pipeline = JudgePipeline(fake_llm, db_path=str(db_file))
    for case in cases:
        result = pipeline.evaluate(case["report"], [])
        assert result == case["scores"]
    pipeline.close()

    conn = sqlite3.connect(db_file)
    rows = conn.execute("SELECT count(*) FROM evaluations").fetchone()[0]
    conn.close()
    assert rows == len(cases)
