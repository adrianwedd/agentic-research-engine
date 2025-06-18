from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from .composite_reward import CompositeRewardFunction, LinearPreferenceModel


class RewardModelTrainer:
    """Train a simple linear reward model with constitution-based labels."""

    def __init__(
        self,
        data_path: str | Path,
        out_dir: str | Path,
        *,
        constitution_path: str | Path | None = None,
        version: str = "",
    ) -> None:
        self.data_path = Path(data_path)
        self.out_dir = Path(out_dir)
        self.constitution_path = Path(constitution_path) if constitution_path else None
        self.version = version
        self.constitution = self._load_constitution() if self.constitution_path else {}

    def load_data(self) -> List[Dict]:
        text = self.data_path.read_text(encoding="utf-8")
        if not text.strip():
            return []
        if text.lstrip()[0] == "[":
            return json.loads(text)
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    @staticmethod
    def preprocess(records: List[Dict]) -> Tuple[List[int], List[float]]:
        """Extract simple length-based features."""
        x = [len(str(rec.get("trace", "")).split()) for rec in records]
        y = [float(rec.get("score", 0)) for rec in records]
        return x, y

    @staticmethod
    def train_model(x: List[int], y: List[float]) -> Dict[str, float]:
        if not x:
            raise ValueError("No training data")
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        denom = sum((xi - mean_x) ** 2 for xi in x) or 1e-8
        a = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / denom
        b = mean_y - a * mean_x
        return {"a": a, "b": b}

    @staticmethod
    def evaluate_model(model: Dict[str, float], x: List[int], y: List[float]) -> float:
        mse = sum(
            (model["a"] * xi + model["b"] - yi) ** 2 for xi, yi in zip(x, y)
        ) / len(y)
        return mse

    def save_model(self, model: Dict[str, float]) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / "preference_model.json"
        path.write_text(json.dumps(model, indent=2), encoding="utf-8")
        return path

    def _load_constitution(self) -> Dict:
        data = yaml.safe_load(self.constitution_path.read_text(encoding="utf-8"))
        return data or {}

    def _self_critique(self, text: str) -> tuple[float, str]:
        banned = [
            t.lower()
            for t in self.constitution.get("policies", {}).get("banned_terms", [])
        ]
        lower = text.lower()
        bad_terms = [t for t in banned if t in lower]
        if bad_terms:
            return 0.0, "contains " + ", ".join(bad_terms)
        return 1.0, "ok"

    def apply_constitution(self, records: List[Dict]) -> List[Dict]:
        if not self.constitution:
            return records
        labeled = []
        for rec in records:
            score, critique = self._self_critique(str(rec.get("trace", "")))
            labeled.append(
                {"trace": rec.get("trace", ""), "score": score, "critique": critique}
            )
        return labeled

    def save_metadata(self, model_path: Path, mse: float) -> Path:
        meta = {
            "version": self.version,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "data_path": str(self.data_path),
            "constitution": str(self.constitution_path)
            if self.constitution_path
            else None,
            "model_file": model_path.name,
            "mse": mse,
        }
        path = self.out_dir / "metadata.json"
        path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return path

    def run(self) -> float:
        records = self.load_data()
        records = self.apply_constitution(records)
        x, y = self.preprocess(records)
        model = self.train_model(x, y)
        mse = self.evaluate_model(model, x, y)
        model_path = self.save_model(model)
        self.save_metadata(model_path, mse)
        self.composite = CompositeRewardFunction(LinearPreferenceModel(model))
        return mse
