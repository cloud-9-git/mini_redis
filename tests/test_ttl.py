from fastapi.testclient import TestClient

import app.routers.kv as kv_router
from app.main import app
from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_ttl_returns_minus_two_for_missing_key() -> None:
    service = KVService(store=InMemoryKVStore())

    assert service.ttl_value("missing:key") == -2


def test_ttl_returns_minus_one_for_existing_key_without_expiration() -> None:
    service = KVService(store=InMemoryKVStore())
    service.set_value("user:ttl", "kim")

    assert service.ttl_value("user:ttl") == -1


def test_ttl_returns_remaining_seconds_for_expiring_key() -> None:
    current_time = {"value": 100.0}
    store = InMemoryKVStore(time_fn=lambda: current_time["value"])
    service = KVService(store=store)

    service.set_value("user:ttl", "kim")
    store.expire("user:ttl", 5.0)

    assert service.ttl_value("user:ttl") == 5


def test_ttl_handles_boundary_before_and_after_expiration() -> None:
    current_time = {"value": 100.0}
    store = InMemoryKVStore(time_fn=lambda: current_time["value"])
    service = KVService(store=store)

    service.set_value("user:boundary", "kim")
    store.expire("user:boundary", 2.0)

    current_time["value"] = 101.9
    assert service.ttl_value("user:boundary") == 0

    current_time["value"] = 102.0
    assert service.ttl_value("user:boundary") == -2
    assert service.get_value("user:boundary") is None
    assert service.exists_value("user:boundary") is False


def test_ttl_endpoint_returns_minus_one_for_existing_key_without_expiration() -> None:
    client = TestClient(app)
    client.post("/v1/kv/set", json={"key": "user:ttl-api", "value": "kim"})

    response = client.get("/v1/kv/ttl", params={"key": "user:ttl-api"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"ttl": -1}}


def test_ttl_endpoint_returns_minus_two_for_missing_key() -> None:
    client = TestClient(app)

    response = client.get("/v1/kv/ttl", params={"key": "missing:key"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"ttl": -2}}


def test_ttl_endpoint_returns_remaining_seconds_for_expiring_key() -> None:
    current_time = {"value": 100.0}
    kv_router.service.store = InMemoryKVStore(time_fn=lambda: current_time["value"])
    client = TestClient(app)

    client.post("/v1/kv/set", json={"key": "user:ttl-api-expiring", "value": "kim"})
    kv_router.service.store.expire("user:ttl-api-expiring", 3.0)

    response = client.get("/v1/kv/ttl", params={"key": "user:ttl-api-expiring"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"ttl": 3}}


def test_ttl_endpoint_returns_minus_two_after_expiration() -> None:
    current_time = {"value": 100.0}
    kv_router.service.store = InMemoryKVStore(time_fn=lambda: current_time["value"])
    client = TestClient(app)

    client.post("/v1/kv/set", json={"key": "user:ttl-api-expired", "value": "kim"})
    kv_router.service.store.expire("user:ttl-api-expired", 1.0)
    current_time["value"] = 101.0

    response = client.get("/v1/kv/ttl", params={"key": "user:ttl-api-expired"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"ttl": -2}}

    get_response = client.get("/v1/kv/get", params={"key": "user:ttl-api-expired"})
    assert get_response.status_code == 404


def test_ttl_endpoint_rejects_empty_key() -> None:
    client = TestClient(app)

    response = client.get("/v1/kv/ttl", params={"key": ""})

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "INVALID_INPUT", "message": "key is required"},
    }
