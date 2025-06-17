import json as jsonlib

from agents.memory_manager import MemoryManagerAgent
from engine.orchestration_engine import GraphState


class DummyClient:
    def __init__(self, output):
        self.output = output

    def invoke(self, _messages, **_kwargs):
        return jsonlib.dumps(self.output)


def test_extract_triples_nested(monkeypatch):
    output = [
        {
            "subject": "Tesla",
            "relations": [
                {"predicate": "FOUNDED_BY", "object": "Elon Musk"},
                {"predicate": "FOUNDED_BY", "object": "Martin Eberhard"},
                {
                    "predicate": "ACQUIRED",
                    "object": "SolarCity",
                    "properties": {"year": 2016},
                },
            ],
        }
    ]
    monkeypatch.setattr(
        "agents.memory_manager.load_llm_client", lambda: DummyClient(output)
    )
    mm = MemoryManagerAgent()
    state = GraphState(data={"report": "Tesla text"})
    triples = mm._extract_triples(state)
    assert {
        "subject": "Tesla",
        "predicate": "FOUNDED_BY",
        "object": "Elon Musk",
    } in triples
    assert {
        "subject": "Tesla",
        "predicate": "FOUNDED_BY",
        "object": "Martin Eberhard",
    } in triples
    assert {
        "subject": "Tesla",
        "predicate": "ACQUIRED",
        "object": "SolarCity",
        "properties": {"year": 2016},
    } in triples


def test_extract_triples_flat(monkeypatch):
    output = [
        {
            "subject": "requests",
            "predicate": "CREATED_BY",
            "object": "Kenneth Reitz",
        },
        {
            "subject": "requests",
            "predicate": "MAINTAINED_BY",
            "object": "open-source community",
        },
    ]
    monkeypatch.setattr(
        "agents.memory_manager.load_llm_client", lambda: DummyClient(output)
    )
    mm = MemoryManagerAgent()
    state = GraphState(data={"report": "Requests"})
    triples = mm._extract_triples(state)
    assert triples == output
