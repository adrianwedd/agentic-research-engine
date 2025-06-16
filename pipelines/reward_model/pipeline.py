from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .composite_reward import CompositeRewardFunction, LinearPreferenceModel


class RewardModelTrainer:
    """Train a simple linear reward model on labeled trajectories."""

    def __init__(self, data_path: str | Path, out_dir: str | Path) -> None:
        self.data_path = Path(data_path)
        self.out_dir = Path(out_dir)

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

    def run(self) -> CompositeRewardFunction:
        records = self.load_data()
        x, y = self.preprocess(records)
        model = self.train_model(x, y)
        self.evaluate_model(model, x, y)
        self.save_model(model)
        preference_model = LinearPreferenceModel(model)
        return CompositeRewardFunction(preference_model)
