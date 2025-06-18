# Governance Process

This repository uses a lightweight governance model centered on an **AI Safety Council**. The council drafts and approves the system constitution stored at the repository root as `constitution.yaml`.

## Constitution Management

1. Proposed changes to the constitution are submitted as pull requests.
2. Each proposal must include rationale and be approved by a majority of the council.
3. Approved versions are tagged and referenced in pipeline metadata.

## Change Requests

All major architectural or policy updates are tracked as change requests in `docs/change_request_ledger.md`. Contributors open a CR with the proposed modification and the council reviews it during scheduled meetings.

## Reward Model Alignment

Training pipelines consume the active constitution to generate self‑critique scores and preference labels. Metadata for each reward model release records the constitution version used so future audits can reproduce training conditions.
