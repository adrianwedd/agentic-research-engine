import importlib.util
import pathlib

import pytest

spec = importlib.util.spec_from_file_location(
    "vector_store",
    pathlib.Path(__file__).resolve().parents[1]
    / "services"
    / "ltm_service"
    / "vector_store.py",
)
vector_store = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(vector_store)
WeaviateVectorStore = vector_store.WeaviateVectorStore


def pytest_collection_modifyitems(config, items):
    for item in items:
        if (
            not item.get_closest_marker("core")
            and not item.get_closest_marker("integration")
            and not item.get_closest_marker("optional")
        ):
            item.add_marker("integration")


@pytest.fixture
def weaviate_vector_store(tmp_path):
    try:
        store = WeaviateVectorStore(persistence_path=str(tmp_path))
    except Exception:
        pytest.skip("weaviate not available")
    yield store
    store.close()
