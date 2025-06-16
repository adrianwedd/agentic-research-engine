# Phase 2 End-to-End Integration Test Report

This report summarizes the results of the full-system tests added in Ticket 2.2. The scenarios exercise the new cognitive faculties introduced in Phase 2.

## Scenario 1 – Learn and Recall
- **Goal:** verify episodic memory recall shortens workflows.
- **Result:** the Supervisor retrieved a past plan for a similar query and reused the template, reducing the plan from three nodes to two.
- **Metric:** plan nodes reduced by one; LTM hit confirmed.

## Scenario 2 – Critique and Correct
- **Goal:** validate the self‑correction loop.
- **Result:** the Evaluator flagged a factual error and the CoSC router retried once before producing a correct report. A second run with the Evaluator forced to fail stopped after the configured retry limit.

## Scenario 3 – Evaluate the Judges
- **Goal:** run the LLM‑as‑a‑Judge pipeline on the golden dataset and compute inter‑rater agreement.
- **Result:** the pipeline evaluated 10 reports and the calibration suite reported mean κ ≈ 0.9.

## Observed Deviations
- The retrieved plan did not always shorten execution unless plan templates were enabled. This aligns with the forgetting strategy discussed in [docs/research/2025-ltm-forgetting-study.md](../research/2025-ltm-forgetting-study.md).

