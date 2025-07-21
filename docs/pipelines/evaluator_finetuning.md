# Evaluator Fine-Tuning Pipeline

This pipeline fine-tunes the Evaluator agent on a synthetic dataset of errors and corrections.
The data lives at `data/synthetic_self_correction/self_correction_dataset.json`.

Run the training script:

```bash
python scripts/train_evaluator.py --model hf-internal-testing/tiny-random-T5 --epochs 1
```

Artifacts are saved under `models/evaluator_finetuned/<version>/` alongside a `metrics.json` file recording the
baseline and fine-tuned accuracy.
