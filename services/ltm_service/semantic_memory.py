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


class SpatioTemporalMemoryService(SemanticMemoryService):
    """Semantic memory with spatio-temporal versioning of facts."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        super().__init__(uri=uri, user=user, password=password)
        self._migrate()

    def _migrate(self) -> None:
        """Convert plain fact records to versioned format if needed."""
        if self._facts is None:
            return
        for fact in self._facts:
            if "history" in fact:
                continue
            props = fact.pop("properties", {})
            version = {
                "value": props.get("value"),
                "valid_from": props.get("valid_from", time.time()),
                "valid_to": props.get("valid_to"),
                "tx_time": props.get("tx_time", time.time()),
                "location": props.get("location"),
            }
            fact["history"] = [version]

    def store_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a fact with an initial version."""
        version = self._build_version(properties or {})
        if self._driver:
            # In this simplified implementation we only support the in-memory
            # backend for versioned facts when the Neo4j driver is not
            # configured. A production implementation would persist versions in
            # Neo4j as node properties or linked records.
            pass
        fact_id = str(uuid.uuid4())
        if self._facts is not None:
            self._facts.append(
                {
                    "id": fact_id,
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "history": [version],
                }
            )
        return fact_id

    @staticmethod
    def _build_version(props: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "value": props.get("value"),
            "valid_from": props.get("valid_from", time.time()),
            "valid_to": props.get("valid_to"),
            "tx_time": props.get("tx_time", time.time()),
            "location": props.get("location"),
        }

    def add_version(
        self,
        fact_id: str,
        *,
        value: Any,
        valid_from: float,
        valid_to: float | None = None,
        tx_time: float | None = None,
        location: Any | None = None,
    ) -> None:
        """Append a new version to the given fact."""
        if self._facts is None:
            return
        for fact in self._facts:
            if fact["id"] == fact_id:
                version = {
                    "value": value,
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "tx_time": tx_time if tx_time is not None else time.time(),
                    "location": location,
                }
                fact.setdefault("history", []).append(version)
                break

    def get_snapshot(self, *, valid_at: float, tx_at: float) -> List[Dict[str, Any]]:
        """Return facts that were valid at the given time with respect to a transaction time."""
        results: List[Dict[str, Any]] = []
        if self._facts is None:
            return results
        for fact in self._facts:
            history = fact.get("history", [])
            chosen: Dict[str, Any] | None = None
            for ver in sorted(history, key=lambda v: v["tx_time"], reverse=True):
                if (
                    ver["tx_time"] <= tx_at
                    and ver["valid_from"] <= valid_at
                    and (ver.get("valid_to") is None or valid_at <= ver["valid_to"])
                ):
                    chosen = ver
                    break
            if chosen:
                results.append(
                    {
                        "id": fact["id"],
                        "subject": fact["subject"],
                        "predicate": fact["predicate"],
                        "object": fact["object"],
                        **chosen,
                    }
                )
        return results
