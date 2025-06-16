# ADR-003: LLM-Grounded Communication Paradigm

This decision formalizes the project's exclusive use of **Guided Evolution** grounded in natural language via an LLM-based signal. Research into "fully emergent" protocols—where agents develop a language entirely from scratch—is deprecated due to instability, poor generalization, and security risks.

## Approved Paradigm
All new communication protocols must be trained with an auxiliary natural-language grounding signal. This ensures the resulting language remains interpretable, auditable, and compatible with zero-shot coordination.

## Deprecated Approach
Any approach that allows agents to invent a protocol from a blank slate without natural-language grounding is disallowed. Existing references remain for historical context only.
