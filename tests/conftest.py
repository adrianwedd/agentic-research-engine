import pytest

from services.ltm_service.vector_store import MilvusVectorStore


def pytest_collection_modifyitems(config, items):
    for item in items:
        if (
            not item.get_closest_marker("core")
            and not item.get_closest_marker("integration")
            and not item.get_closest_marker("optional")
        ):
            item.add_marker("integration")


@pytest.fixture()
def milvus_vector_store(tmp_path):
    try:
        store = MilvusVectorStore(persistence_path=str(tmp_path / "milvus"))
    except Exception as exc:  # pragma: no cover - skip if dependencies missing
        pytest.skip(f"milvus not available: {exc}")
    yield store
    store.close()
