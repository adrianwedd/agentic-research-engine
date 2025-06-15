from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Callable, Dict, List

from jsonschema import validate
from tenacity import retry, stop_after_attempt, wait_exponential


class JudgePipeline:
    """LLM-as-a-Judge evaluation pipeline."""

    def __init__(
        self,
        llm: Callable[[str], str],
        db_path: str = "results.db",
        rubric_path: str
        | Path = Path(__file__).resolve().parents[2] / "schemas" / "judge_rubric.json",
        alert_fn: Callable[[Exception], None] | None = None,
    ) -> None:
        self.llm = llm
        self.db_path = db_path
        self.alert_fn = alert_fn
        self.rubric = json.loads(Path(rubric_path).read_text(encoding="utf-8"))
        self._ensure_db()

    def _ensure_db(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        with self.conn:
            self.conn.execute(
                (
                    "CREATE TABLE IF NOT EXISTS evaluations "
                    "(id INTEGER PRIMARY KEY AUTOINCREMENT, report TEXT, result TEXT)"
                )
            )

    def close(self) -> None:
        self.conn.close()

    def _build_prompt(self, report: str, sources: List[str]) -> str:
        rubric = json.dumps(self.rubric, indent=2)
        joined = "\n".join(sources)
        return (
            "You are an impartial judge evaluating a research report.\n"
            "Report:\n" + report + "\n"
            "Sources:\n" + joined + "\n"
            "Using the rubric JSON schema:\n" + rubric + "\n"
            "Respond ONLY with valid JSON matching that schema."
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4)
    )
    def _call_llm(self, prompt: str) -> str:
        return self.llm(prompt)

    def evaluate(self, report: str, sources: List[str]) -> Dict:
        prompt = self._build_prompt(report, sources)
        try:
            response = self._call_llm(prompt)
        except Exception as e:  # persistent failure
            if self.alert_fn:
                self.alert_fn(e)
            raise
        data = json.loads(str(response))
        validate(instance=data, schema=self.rubric)
        with self.conn:
            self.conn.execute(
                "INSERT INTO evaluations (report, result) VALUES (?, ?)",
                (report, json.dumps(data)),
            )
        return data
