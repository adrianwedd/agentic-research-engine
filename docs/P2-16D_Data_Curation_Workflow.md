# Dataset Curation & Validation Workflow (P2-16D)

Synthetic data used for Evaluator training must be curated before any fine tuning occurs. This document describes the workflow implemented in `scripts/dataset_curation.py`.

## Automated Validation
1. Run `python scripts/dataset_curation.py <dataset.json>`.
2. The script validates each record:
   - Ensures required fields are present.
   - Flags examples where `erroneous_version` matches `corrected_version`.
   - Deduplicates identical entries.
3. Invalid records are written to `invalid_records.json` inside a versioned folder.

## Human Review Sampling
After validation, 5% of the curated records are shown for manual rating. Reviewers rate the realism of the error and correction on a 1–5 scale. Ratings are stored in `human_review.json` in the same versioned folder.

## Versioning
The curated dataset is saved to `data/curated/<timestamp>/dataset.json`. The timestamp serves as the version identifier and should be logged when launching training jobs so results can be traced back to a specific dataset version.
