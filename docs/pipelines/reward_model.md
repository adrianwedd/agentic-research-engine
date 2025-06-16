# Reward Model Training Pipeline

This pipeline trains a simple reward model using the quality scores produced by the LLM-as-a-Judge evaluation step. The dataset should contain JSON records with a `trace` field (the task execution trace) and a numeric `score`.

The `RewardModelTrainer` extracts lightweight features from the trace (currently just token length), fits a linear regression model, and saves the coefficients to `reward_model.json` in the specified output directory.

Run the training script:

```bash
python scripts/train_reward_model.py --data-path data/evaluated_traces.json
```

The script versions models under `models/reward_model/<timestamp>/` and prints the evaluation MSE.
