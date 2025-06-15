from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


# ``services.learning`` imports the optional ``trl`` dependency. Import lazily
# to avoid hard failures when the library is unavailable (tests will skip).
def _load_learning_modules():
    from services.learning import PPOPolicyOptimizer, RLAIFSystem

    return PPOPolicyOptimizer, RLAIFSystem


class RewardModel:
    """Lightweight linear reward model loader."""

    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.weights = json.loads(self.model_path.read_text(encoding="utf-8"))

    def score(self, trajectory: Dict) -> float:
        a = float(self.weights.get("a", 0))
        b = float(self.weights.get("b", 0))
        length = len(str(trajectory.get("response", "")).split())
        return a * length + b


class SupervisorPolicyTrainer:
    """Run RLAIF to update the Supervisor's planning policy."""

    def __init__(
        self,
        data_path: str | Path,
        reward_model_path: str | Path,
        model_name: str = "sshleifer/tiny-gpt2",
        out_dir: str | Path = "models/supervisor_policy",
    ) -> None:
        self.data_path = Path(data_path)
        self.reward_model = RewardModel(reward_model_path)
        PPOPolicyOptimizer, RLAIFSystem = _load_learning_modules()
        self.rlaif = RLAIFSystem(
            self.reward_model,
            PPOPolicyOptimizer(model_name, log_dir=out_dir),
        )

    def load_data(self) -> List[Dict]:
        text = self.data_path.read_text(encoding="utf-8")
        if text.lstrip().startswith("["):
            return json.loads(text)
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def run(self, epochs: int = 1) -> Dict[str, float]:
        records = self.load_data()
        for _ in range(max(1, epochs)):
            batch = [
                {"prompt": rec.get("query", ""), "response": rec.get("plan", "")}
                for rec in records
            ]
            self.rlaif.update_agent_policies(batch)
        return self.rlaif.metrics
