import pytest
from httpx import ASGITransport, AsyncClient

from services.evaluation.app import _STORE, app


@pytest.fixture(autouse=True)
def clear_store():
    _STORE.clear()
    yield
    _STORE.clear()


@pytest.mark.asyncio
async def test_auth_required():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/evaluator_memory", json={"critique": {"a": 1}})
        assert resp.status_code == 401

        resp = await client.get("/evaluator_memory")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": "Bearer wrong"}
        resp = await client.post(
            "/evaluator_memory", json={"critique": {"a": 1}}, headers=headers
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_store_and_retrieve():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": "Bearer eval-token"}
        resp = await client.post(
            "/evaluator_memory", json={"critique": {"a": 1}}, headers=headers
        )
        assert resp.status_code in (200, 201)
        cid = resp.json()["id"]

        resp = await client.request(
            "GET",
            "/evaluator_memory",
            params={"limit": 1},
            json={"query": {"id": cid}},
            headers=headers,
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert results and results[0]["id"] == cid
