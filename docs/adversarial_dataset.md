# Adversarial Edge-Case Dataset

This folder stores a curated set of adversarial examples targeting known weaknesses of the Evaluator agent. All files live under `data/adversarial_examples/`.

## Curation Process
1. Identified common failure modes such as percentage misreads, date format confusion, unit swaps, logical fallacies, and historical year mistakes.
2. Wrote the script `scripts/generate_adversarial_examples.py` to automatically produce examples exhibiting these errors alongside short critiques.
3. Generated 50 total records (10 per category) with a fixed random seed for reproducibility.

## File Overview
- `edge_cases.json` – JSON list of adversarial examples used to harden the Evaluator.
- `generate_adversarial_examples.py` – Script that creates the dataset.
