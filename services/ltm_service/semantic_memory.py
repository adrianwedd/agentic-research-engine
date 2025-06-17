from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - fallback if driver missing
    GraphDatabase = None


class SemanticMemoryService:
    """Semantic memory backed by Neo4j with in-memory fallback."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self._facts: List[Dict[str, Any]] | None = None
        self._driver = None
        uri = uri or os.getenv("NEO4J_URI")
        user = user or os.getenv("NEO4J_USER")
        password = password or os.getenv("NEO4J_PASSWORD")
        if GraphDatabase and uri and user and password:
            try:
                self._driver = GraphDatabase.driver(uri, auth=(user, password))
            except Exception:  # pragma: no cover - connection failure
                self._driver = None
        if self._driver is None:
            self._facts = []

    def run_cypher(
        self, query: str, parameters: Optional[Dict[str, Any]] | None = None
    ) -> List[Dict[str, Any]]:
        """Execute an arbitrary Cypher query when a driver is available."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not configured")
        with self._driver.session() as session:
            records = session.run(query, parameters or {})
            return [rec.data() for rec in records]

    def store_jsonld(self, data: Dict[str, Any]) -> List[str]:
        """Persist a JSON-LD payload as one or more facts."""

        def _iter_triples(item: Dict[str, Any]) -> List[Dict[str, Any]]:
            triples = []
            graph = item.get("@graph")
            if graph:
                for entry in graph:
                    triples.extend(_iter_triples(entry))
                return triples

            if {"subject", "predicate", "object"} <= item.keys():
                triple = {
                    "subject": item["subject"],
                    "predicate": item["predicate"],
                    "object": item["object"],
                    "properties": item.get("properties", {}),
                }
                triples.append(triple)
            return triples

        ids: List[str] = []
        for triple in _iter_triples(data):
            ids.append(
                self.store_fact(
                    triple["subject"],
                    triple["predicate"],
                    triple["object"],
                    properties=triple.get("properties"),
                )
            )
        return ids

    def store_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        props = properties or {}
        if self._driver:
            query = """
                MERGE (s:Entity {name: $subject})
                MERGE (o:Entity {name: $object})
                MERGE (s)-[r:RELATION {type: $predicate}]->(o)
                SET r += $props
                RETURN id(r) AS rid
                """
            with self._driver.session() as session:
                record = session.run(
                    query,
                    subject=subject,
                    object=obj,
                    predicate=predicate,
                    props=props,
                ).single()
                return str(record["rid"])
        fact_id = str(uuid.uuid4())
        if self._facts is not None:
            self._facts.append(
                {
                    "id": fact_id,
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "properties": props,
                }
            )
        return fact_id

    def query_facts(
        self,
        *,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if self._driver:
            query = """
                MATCH (s:Entity)-[r:RELATION]->(o:Entity)
                WHERE ($subject IS NULL OR s.name = $subject)
                  AND ($predicate IS NULL OR r.type = $predicate)
                  AND ($object IS NULL OR o.name = $object)
                  AND (r.deleted_at IS NULL)
                RETURN id(r) AS id, s.name AS subject, r.type AS predicate,
                       o.name AS object, r AS rel
                """
            with self._driver.session() as session:
                records = session.run(
                    query,
                    subject=subject,
                    predicate=predicate,
                    object=object,
                )
                return [
                    {
                        "id": str(rec["id"]),
                        "subject": rec["subject"],
                        "predicate": rec["predicate"],
                        "object": rec["object"],
                        "properties": dict(rec["rel"]),
                    }
                    for rec in records
                ]
        results = []
        if self._facts is None:
            return results
        for fact in self._facts:
            if fact.get("deleted_at"):
                continue
            if subject and fact["subject"] != subject:
                continue
            if predicate and fact["predicate"] != predicate:
                continue
            if object and fact["object"] != object:
                continue
            results.append(fact)
        return results

    def forget_fact(self, fact_id: str, *, hard: bool = False) -> bool:
        if self._driver:
            try:
                rid = int(fact_id)
            except ValueError:
                return False
            if hard:
                query = "MATCH ()-[r]->() WHERE id(r)=$id DELETE r RETURN count(r) AS c"
                with self._driver.session() as session:
                    rec = session.run(query, id=rid).single()
                    return bool(rec and rec["c"])
            query = "MATCH ()-[r]->() WHERE id(r)=$id SET r.deleted_at=$ts RETURN count(r) AS c"
            with self._driver.session() as session:
                rec = session.run(query, id=rid, ts=time.time()).single()
                return bool(rec and rec["c"])
        if self._facts is None:
            return False
        for fact in list(self._facts):
            if fact["id"] != fact_id:
                continue
            if hard:
                self._facts.remove(fact)
            else:
                fact["deleted_at"] = time.time()
            return True
        return False

    def close(self) -> None:
        if self._driver:
            self._driver.close()
