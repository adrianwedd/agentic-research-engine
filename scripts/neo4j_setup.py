import os

from neo4j import GraphDatabase

INDEX_QUERIES = [
    "CREATE INDEX valid_from_index IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.valid_from)",
    "CREATE INDEX valid_to_index IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.valid_to)",
    "CREATE INDEX tx_time_index IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.tx_time)",
    "CREATE INDEX location_index IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.location)",
]


def create_indexes() -> None:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not (uri and user and password):
        print("NEO4J credentials not set, skipping index creation")
        return
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        for query in INDEX_QUERIES:
            session.run(query)
    driver.close()
    print("Neo4j indexes ensured")


if __name__ == "__main__":
    create_indexes()
