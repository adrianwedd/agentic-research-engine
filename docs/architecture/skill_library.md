# SkillLibrary Data Model

The SkillLibrary stores reusable policies that can be retrieved via vector search or metadata filtering.
Each skill entry contains the following fields:

- `skill_policy` – arbitrary JSON describing the policy implementation.
- `skill_representation` – text or vector representation used for embedding.
- `skill_metadata` – dictionary of metadata used for filtering.

Skills are embedded using the configured embedding client and indexed in the vector store. The service exposes endpoints for adding skills and querying them either by embedding similarity or by metadata filters.
