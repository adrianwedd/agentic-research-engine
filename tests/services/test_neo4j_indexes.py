import os

import pytest

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - driver optional
    GraphDatabase = None


@pytest.mark.integration
def test_temporal_indexes_exist():
    if GraphDatabase is None:
        pytest.skip("neo4j driver not installed")
    if not (
        os.getenv("NEO4J_URI")
        and os.getenv("NEO4J_USER")
        and os.getenv("NEO4J_PASSWORD")
    ):
        pytest.skip("neo4j not configured")

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        records = session.run(
            """
            SHOW INDEXES YIELD entityType, labelsOrTypes, properties
            WHERE entityType = 'RELATIONSHIP' AND labelsOrTypes = ['RELATION']
            RETURN properties
            """
        )
        props = {tuple(r["properties"]) for r in records}
    driver.close()

    expected = {
        ("valid_from",),
        ("valid_to",),
        ("tx_time",),
        ("location",),
    }
    assert expected <= props
