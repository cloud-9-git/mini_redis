from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_regression_core_kv_flow() -> None:
    client = TestClient(app)
    set_response = client.post("/v1/kv/set", json={"key": "user:regression", "value": "v1"})
    get_response = client.get("/v1/kv/get", params={"key": "user:regression"})
    del_response = client.delete("/v1/kv/del", params={"key": "user:regression"})

    assert set_response.status_code == 200
    assert get_response.status_code == 200
    assert del_response.status_code == 200
    assert del_response.json() == {"success": True, "data": {"deleted": True}}


def test_regression_ttl_flow() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:ttl-regression", "value": "v2"})
    expire_response = client.post("/v1/kv/expire", json={"key": "user:ttl-regression", "seconds": 10})
    ttl_response = client.get("/v1/kv/ttl", params={"key": "user:ttl-regression"})
    persist_response = client.post("/v1/kv/persist", json={"key": "user:ttl-regression"})

    assert expire_response.status_code == 200
    assert ttl_response.status_code == 200
    assert ttl_response.json()["data"]["ttl"] >= 1
    assert persist_response.status_code == 200


def test_regression_invalidate_and_metrics_flow() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:inv:1", "value": "A"})
    client.post("/v1/kv/set", json={"key": "user:inv:2", "value": "B"})
    invalidate_response = client.post("/v1/kv/invalidate-prefix", json={"prefix": "user:inv:"})
    metrics_response = client.get("/v1/metrics/cache")

    assert invalidate_response.status_code == 200
    assert invalidate_response.json()["data"]["deletedCount"] >= 1
    assert metrics_response.status_code == 200
    assert metrics_response.json()["success"] is True


def test_regression_system_readiness_endpoint_exists(monkeypatch) -> None:
    monkeypatch.setenv("RELEASE_READY", "false")
    client = TestClient(app)
    response = client.get("/v1/system/readiness")

    assert response.status_code == 200
    assert response.json()["success"] is True
