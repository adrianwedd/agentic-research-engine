# Self-Correction Synthetic Data Research (P2-15A)

This document summarizes a research spike comparing methods to generate synthetic error/correction pairs for training the Evaluator agent. Two prototype approaches were implemented and assessed on short research summaries.

## Candidate Methods

1. **Teacher-student perturbation** – a powerful teacher model creates a correct answer which is then intentionally corrupted (e.g. by modifying facts or structure). The student model learns to critique and fix these flawed answers.
2. **Back-translation noise** – content is translated to another language and back. Imperfect translations introduce lexical and syntactic errors.
3. **Adversarial typos** – simple character swaps simulate common transcription or OCR errors.

Academic sources highlight the effectiveness of teacher-student setups for creating diverse errors while maintaining semantic coherence. Back-translation is widely used in data augmentation pipelines, though quality varies by language pair.

## Prototype Evaluation

A small script (`scripts/generate_synthetic_examples.py`) produced sample pairs from two research snippets. Back-translation used Russian as the intermediate language via `googletrans`. Typos were injected at a 10% rate.

`data/synthetic_self_correction/sample_pairs.json` stores the outputs. Example entry:

```json
{
  "original": "Long-Term Memory Consolidation & Forgetting Research (P2-19A)...",
  "back_translation": "Long-term memory consolidation and forgetting research (P2-19A)...",
  "typo_perturbation": "... the Long-Term Memory (LTM) sevrice ..."
}
```

A brief human review found back-translated text preserved meaning but contained awkward phrasing. Typos were trivial but may help with robustness. Generation costs were minimal (~1s per example) but the quality of the teacher‑student approach would depend on API pricing for a large model.

## Recommendation

For P2‑16A, a **teacher-student pipeline** is preferred: leverage a strong model to generate pristine solutions, then automatically perturb them (via back‑translation and adversarial edits) to create realistic errors. This balances diversity with controllable cost and scales well for thousands of examples.

