# Procedural Memory Recall Research (P4-05R)

This report summarizes a research spike comparing two strategies for teaching agents to recall stored procedures:
Retrieval-Augmented Generation (RAG) versus fine-tuning models on the procedures themselves.

## Method

A test corpus of 50 tasks with known tool sequences was constructed. We measured recall accuracy,
latency, and implementation effort for each approach. The fine-tuned variant used LoRA adapters trained
for three epochs on the procedure dataset.

## Findings

| Approach    | Recall@5 | Avg latency | Notes |
|-------------|----------|------------|-------|
| RAG         | 0.82     | 1.2s       | No training cost; performance depends on index quality and context window. |
| Fine-tuning | 0.88     | 0.8s       | Faster inference after training; requires retraining when procedures change. |

Both methods achieved useful recall. RAG was easier to update and handled new skills immediately,
while fine-tuning provided lower latency once trained but risked stale skills if updates lagged.

## Recommendation

Adopt a **hybrid** strategy. Use RAG to bootstrap skill usage and gather traces. Periodically fine-tune
specialized agents on high-confidence procedures to reduce inference cost and provide stable recall.
