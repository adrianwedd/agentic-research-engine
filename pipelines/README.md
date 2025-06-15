# Pipelines Directory

This folder contains workflow definitions for continuous integration and deployment. The CD pipeline relies on Terraform and Helm configuration stored under `../infra` to roll out services using a rainbow deployment strategy.

## CI Pipeline Overview

The `ci.yml` workflow installs dependencies with pip caching and caches the pre-commit environments. Lint and test jobs run in parallel to speed up feedback. The `codex-sanity` job validates repository layout and executes the full test suite.

Branch protection rules should require all CI jobs to pass and at least one approving review before merging into `main`.
