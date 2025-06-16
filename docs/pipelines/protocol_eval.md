# Protocol Evaluation Pipeline

This pipeline measures the quality of emergent communication.
It exposes helper functions to compute:

- **Zero-Shot Coordination (ZSC) Score** – average reward when agents from independent runs are paired together.
- **Causal Influence of Communication (CIC)** – mutual information between a sent message and the receiver's next action.
- **Interpretability Score** – cosine similarity between message vectors and their target natural language concepts.

The metrics can be imported from `services.evaluation` and composed into more complex evaluation suites.
