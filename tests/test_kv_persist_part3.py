import time

from fastapi.testclient import TestClient

from app.main import app
from app.stores.kv_store import InMemoryKVStore


def test_persist_returns_false_when_key_is_missing() -> None:
    client = TestClient(app)
    response = client.post("/v1/kv/persist", json={"key": "user:missing"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"updated": False}}


def test_persist_returns_false_when_key_has_no_expiration() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:no-ttl", "value": "kim"})
    response = client.post("/v1/kv/persist", json={"key": "user:no-ttl"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"updated": False}}


def test_persist_removes_expiration_and_keeps_value_alive() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:keep", "value": "kim"})
    client.post("/v1/kv/expire", json={"key": "user:keep", "seconds": 1})

    persist_response = client.post("/v1/kv/persist", json={"key": "user:keep"})
    assert persist_response.status_code == 200
    assert persist_response.json() == {"success": True, "data": {"updated": True}}

    time.sleep(1.1)
    ttl_response = client.get("/v1/kv/ttl", params={"key": "user:keep"})
    get_response = client.get("/v1/kv/get", params={"key": "user:keep"})

    assert ttl_response.status_code == 200
    assert ttl_response.json() == {"success": True, "data": {"ttl": -1}}
    assert get_response.status_code == 200
    assert get_response.json() == {
        "success": True,
        "data": {"key": "user:keep", "value": "kim"},
    }


def test_persist_fails_after_key_already_expired() -> None:
    store = InMemoryKVStore()
    store.set("user:late", "kim")
    store.expire("user:late", 1)
    time.sleep(1.1)

    assert store.persist("user:late") is False
    assert store.ttl("user:late") == -2
    assert store.get("user:late") is None
