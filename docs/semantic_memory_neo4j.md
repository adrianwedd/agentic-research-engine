# Semantic Memory with Neo4j

This guide explains how to connect the Long-Term Memory (LTM) service to a Neo4j graph
database so that verified facts can be stored as nodes and relationships.

## Prerequisites

- A running Neo4j instance (local or remote)
- `neo4j` Python driver installed:
  ```bash
  pip install neo4j
  ```
- Environment variables for the connection URL and credentials:
  - `NEO4J_URI` (e.g. `bolt://localhost:7687`)
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`

## Connecting from the LTM service

Configure the LTM service to create a Neo4j driver during start-up and use it to
persist semantic facts. A minimal setup looks like this:

```python
from neo4j import GraphDatabase

class SemanticMemory:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self._driver.close()
```

## Creating nodes and relationships

The following helper stores a `(subject)-[predicate]->(object)` triple while
avoiding duplicate nodes:

```python
class SemanticMemory:
    # ...
    def store_fact(self, subject: str, predicate: str, obj: str) -> None:
        query = """
        MERGE (s:Entity {name: $subject})
        MERGE (o:Entity {name: $object})
        MERGE (s)-[r:RELATION {type: $predicate}]->(o)
        RETURN id(r)
        """
        with self._driver.session() as session:
            session.run(query, subject=subject, object=obj, predicate=predicate)
```

`MERGE` ensures that existing nodes with the same `name` are reused instead of
duplicated. Relationships of the same `type` between the two nodes are also
collapsed into a single edge.

Once connected, the LTM service can call `store_fact()` whenever the
MemoryManager extracts a new fact from verified research outputs.

## API endpoint

Facts can also be written via the `/semantic_consolidate` HTTP endpoint of the
LTM service. Send either a JSON-LD object describing the triple or a raw Cypher
statement:

```bash
curl -X POST http://localhost:8081/semantic_consolidate \
     -H 'Content-Type: application/json' \
     -d '{"payload": {"subject": "Transformer", "predicate": "IS_A", "object": "Model"}}'
```

## Migration Notes

Earlier releases bundled a local Weaviate instance for episodic memory. The
service now expects an external vector database. Configure the endpoint via
`WEAVIATE_URL` (and optional `WEAVIATE_API_KEY`). The Neo4j setup described
above is unaffected.
