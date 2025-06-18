import json
from pathlib import Path  # noqa: F401

from pipelines.reward_model import LinearPreferenceModel, train_from_preferences
from services.learning.rlaif_system import RLAIFSystem


class CountingOptimizer:
    def __init__(self):
        self.total = 0.0

    def update(self, experience, reward):
        self.total += reward
        return -reward


def test_preference_training_updates_policy(tmp_path):
    pref = {"better": "long answer", "worse": "short"}
    pref_file = tmp_path / "prefs.jsonl"
    pref_file.write_text(json.dumps(pref) + "\n", encoding="utf-8")
    out_dir = tmp_path / "model"
    train_from_preferences(pref_file, out_dir)
    model = LinearPreferenceModel.from_file(out_dir / "preference_model.json")
    opt = CountingOptimizer()
    rlaif = RLAIFSystem(model, opt)
    rlaif.update_agent_policies([{"prompt": "Q", "response": "short"}])
    before = opt.total
    rlaif.update_agent_policies([{"prompt": "Q", "response": "long answer"}])
    after = opt.total
    assert after > before


def test_active_querying_triggers_callback():
    called = []

    class ZeroReward:
        def score(self, exp):
            return 0.0

    class DummyOpt:
        def update(self, exp, reward):
            return 0.0

    def cb(exp):
        called.append(exp)

    rlaif = RLAIFSystem(
        ZeroReward(), DummyOpt(), feedback_callback=cb, active_query_threshold=0.5
    )
    rlaif.update_agent_policies([{"prompt": "p", "response": "r"}])
    assert called
