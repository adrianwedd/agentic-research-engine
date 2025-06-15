from pipelines.judge.pipeline import JudgePipeline


def test_pipeline_evaluates_and_persists(tmp_path):
    calls = []

    def fake_llm(prompt: str) -> str:
        calls.append(prompt)
        return (
            '{"factual_accuracy": {"score": 1.0}, "completeness": {"score": 0.9},'
            ' "source_quality": {"score": 0.8}, "coherence": {"score": 0.95}}'
        )

    db_file = tmp_path / "results.db"
    pipeline = JudgePipeline(fake_llm, db_path=str(db_file))
    report = "Sample report"
    sources = ["Source 1"]
    result = pipeline.evaluate(report, sources)
    pipeline.close()

    assert result["coherence"]["score"] == 0.95
    # Verify persistence
    import sqlite3

    conn = sqlite3.connect(db_file)
    rows = conn.execute("SELECT count(*) FROM evaluations").fetchone()[0]
    assert rows == 1
    conn.close()
    assert calls, "LLM should have been called"


def test_pipeline_retries_on_failure(tmp_path):
    attempts = []

    def flaky_llm(prompt: str) -> str:
        attempts.append(1)
        if len(attempts) < 2:
            raise RuntimeError("temp error")
        return (
            '{"factual_accuracy": {"score": 0.9}, "completeness": {"score": 1.0},'
            ' "source_quality": {"score": 1.0}, "coherence": {"score": 1.0}}'
        )

    db_file = tmp_path / "results.db"
    pipeline = JudgePipeline(flaky_llm, db_path=str(db_file))
    out = pipeline.evaluate("R", ["S"])
    pipeline.close()
    assert out["factual_accuracy"]["score"] == 0.9
    assert len(attempts) == 2
