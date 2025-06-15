# Golden Judge Dataset

This folder contains the manually annotated dataset used for calibrating the LLM-as-a-Judge pipeline. All files live under `data/golden_judge_dataset/`.

## Curation Process
1. Twenty research reports were sampled from prior system runs.
2. Two expert annotators independently scored each report using the rubric defined in `schemas/judge_rubric.json`.
3. Inter-annotator agreement was calculated using Cohen's Kappa on the rounded scores.
4. Disagreements were resolved in an adjudication session to produce the final labels stored in `golden_dataset.json`.

The computed agreement metrics were:
- `factual_accuracy`: 0.86
- `completeness`: 0.92
- `source_quality`: 0.78
- `coherence`: 0.72
- **Mean kappa**: 0.82

All values exceed the target threshold of 0.7.

## Annotator Guidelines
Annotators rated each criterion on a 0–1 scale, optionally providing a justification. Scores were rounded to one decimal place for agreement analysis. Example valid objects can be found in `docs/judge_rubric_examples.md`.

## File Overview
- `golden_dataset.json` – Final adjudicated scores for all 20 reports.
- `annotations.csv` – Raw scores from both annotators prior to adjudication.

