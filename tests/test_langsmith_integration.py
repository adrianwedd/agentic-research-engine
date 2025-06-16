import asyncio

from engine.orchestration_engine import GraphState, create_orchestration_engine
from services.tracing.langsmith_integration import LangSmithCheckpointer, import_dataset


class DummyClient:
    def __init__(self) -> None:
        self.datasets = {}
        self.examples = []
        self.runs = []

    # dataset methods
    def has_dataset(self, dataset_name: str) -> bool:
        return dataset_name in self.datasets

    def create_dataset(self, dataset_name: str):
        self.datasets[dataset_name] = {"id": dataset_name}
        return type("DS", (), {"id": dataset_name})

    def create_example(self, *, inputs, outputs, dataset_id):
        self.examples.append((dataset_id, inputs, outputs))

    # run methods
    def create_run(self, name, inputs, run_type, **kwargs):
        self.runs.append({"name": name, "inputs": inputs, "kwargs": kwargs})


def test_import_dataset_creates_examples(tmp_path):
    client = DummyClient()
    import_dataset("benchmarks/browsecomp/dataset_v1.json", "TestSet", client)
    assert "TestSet" in client.datasets
    assert client.examples


def test_orchestration_checkpointer_logs_runs():
    client = DummyClient()
    cp = LangSmithCheckpointer(client, project_name="p")

    engine = create_orchestration_engine()
    engine.checkpointer = cp
    engine.add_node("A", lambda s, sp: s)

    asyncio.run(engine.run_async(GraphState(), thread_id="t"))
    assert any(r["name"] == "A" for r in client.runs)
