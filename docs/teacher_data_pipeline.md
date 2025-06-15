# Teacher LLM Data Generation Pipeline

This document describes the pipeline used to create synthetic self-correction examples for the Evaluator agent.

The pipeline prompts a powerful "teacher" model with a short topic. The model must reply with a JSON object containing:

- `original_problem`
- `flawed_output`
- `detailed_critique`
- `corrected_solution`

Results are stored under `data/teacher_dataset/`.
