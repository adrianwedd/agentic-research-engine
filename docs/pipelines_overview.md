# Pipeline Overview

This repository includes several small pipelines that generate training data, evaluate model outputs, and update agent policies. They are implemented under the `pipelines/` package and can be invoked via scripts in `scripts/`.

1. **Teacher Data Generation** – `TeacherDataPipeline` prompts a large model to create self‑correction examples and saves them under `data/teacher_dataset/`.
2. **Back Translation Augmentation** – `BackTranslationPipeline` introduces linguistic noise by translating the teacher data to another language and back.
3. **Evaluator Fine‑Tuning** – `train_evaluator.py` fine‑tunes the Evaluator model on the synthetic error/correction pairs.
4. **Judge Evaluation** – `JudgePipeline` scores research reports against `schemas/judge_rubric.json` and persists the results.
5. **Reward Model Training** – `RewardModelTrainer` fits a simple linear model using the judged scores (and optional constitution labels).
6. **Supervisor Policy Training** – `SupervisorPolicyTrainer` runs RLAIF with the reward model to refine the Supervisor's planning policy.
7. **Multi‑Agent Fine‑Tuning** – `MultiAgentFinetunePipeline` fine‑tunes multiple agent policies in parallel using the same reward model.

Each stage consumes artifacts from the previous steps and writes versioned outputs under `data/` or `models/`. Individual pipelines can also be composed in higher‑level workflows.

