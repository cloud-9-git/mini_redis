from fastapi.testclient import TestClient

from app.main import app


def test_expire_ttl_and_persist_scaffold_flow() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:ttl", "value": "kim"})

    expire_response = client.post("/v1/kv/expire", json={"key": "user:ttl", "seconds": 60})
    assert expire_response.status_code == 200
    assert expire_response.json() == {"success": True, "data": {"updated": True}}

    ttl_response = client.get("/v1/kv/ttl", params={"key": "user:ttl"})
    assert ttl_response.status_code == 200
    assert ttl_response.json()["success"] is True
    assert isinstance(ttl_response.json()["data"]["ttl"], int)
    assert ttl_response.json()["data"]["ttl"] >= 1

    persist_response = client.post("/v1/kv/persist", json={"key": "user:ttl"})
    assert persist_response.status_code == 200
    assert persist_response.json() == {"success": True, "data": {"updated": True}}

    ttl_after_persist = client.get("/v1/kv/ttl", params={"key": "user:ttl"})
    assert ttl_after_persist.status_code == 200
    assert ttl_after_persist.json() == {"success": True, "data": {"ttl": -1}}


def test_expire_rejects_non_positive_seconds() -> None:
    client = TestClient(app)
    response = client.post("/v1/kv/expire", json={"key": "user:ttl", "seconds": 0})

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "TTL_INVALID", "message": "seconds must be a positive integer"},
    }
