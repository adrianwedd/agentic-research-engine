# Spatio-Temporal Memory Research

The project explored how to extend the Long-Term Memory (LTM) service with explicit models of time and location. The proposed **Spatio-Temporal Memory** combines bitemporal indexing with spatial coordinates so facts can be queried by when and where they are true.

## Data Model Overview
- Nodes represent entities and events.
- Each node stores a list of versions with `valid_from`, `valid_to`, and `location` fields.
- Locations are indexed using GeoJSON coordinates, enabling spatial range searches.
- Separate transaction timestamps track when observations were ingested.

## API Endpoints
- `POST /temporal_consolidate` – Ingests new observations and merges them into the bitemporal history.
- `GET /spatial_query` – Retrieves nodes within a geographic boundary and time range.

## Related Work
The design draws on cognitive architectures like ACT-R and Soar that segment episodic memory by context. Prior art in temporal knowledge graphs and event-centric models informed the bitemporal property graph approach.

## Proposed Epic: Spatio-Temporal Memory Expansion
1. **CR-ST-01 – Bitemporal Graph Schema**
   - Implement node versioning with valid and transaction times plus GeoJSON locations.
2. **CR-ST-02 – Consolidation Endpoint**
   - Add `/temporal_consolidate` API for batch ingestion of timestamped facts.
3. **CR-ST-03 – Spatial Query Service**
   - Expose `/spatial_query` for bounding-box searches over time intervals.
4. **CR-ST-04 – Indexing & Performance**
   - Create composite indexes on time and location fields to enable efficient queries.
5. **CR-ST-05 – Cross-Agent Reasoning**
   - Update retrieval workflows so agents can reason over time and place when planning tasks.

#### Works cited
1. ACT-R: A Theory of Higher Level Cognition and Its Relation to Visual Attention. <https://doi.org/10.1016/S1364-6613(00)01500-8>
2. Soar Cognitive Architecture. <https://doi.org/10.1017/S0140525X00005756>
3. A Survey on Temporal Knowledge Graphs. <https://arxiv.org/abs/2403.04782>
