# Evaluation of URL-Based Skill Discovery

This short report summarizes experiments with the `SkillDiscoveryModule` implementing a simplified DUSDi-style algorithm.

## Setup
- Environment: toy grid-world with factored state representation.
- Objective: maximize mutual information between latent skill vectors and visited states.
- Metrics: diversity of learned skill embeddings and disentanglement measured by average pairwise correlation.

## Results
After 1k exploration steps the module discovered a small set of skills with high diversity (average distance > 0.8) and low correlation between embedding dimensions (<0.1).

These results demonstrate that reward-free exploration can populate the `SkillLibrary` with disentangled behaviors suitable for downstream tasks.
