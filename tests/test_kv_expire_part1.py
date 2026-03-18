import pytest
from fastapi.testclient import TestClient

from app.core.errors import APIError
from app.main import app
from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_expire_service_sets_ttl_for_existing_key() -> None:
    store = InMemoryKVStore()
    service = KVService(store=store)
    store.set("user:expire:1", "kim")

    updated = service.expire_value("user:expire:1", 5)

    assert updated is True
    ttl = store.ttl("user:expire:1")
    assert 1 <= ttl <= 5


@pytest.mark.parametrize("seconds", [0, -1, -10])
def test_expire_service_rejects_non_positive_seconds(seconds: int) -> None:
    service = KVService(store=InMemoryKVStore())

    with pytest.raises(APIError) as exc_info:
        service.expire_value("user:expire:1", seconds)

    assert exc_info.value.code == "TTL_INVALID"
    assert exc_info.value.status_code == 400
    assert exc_info.value.message == "seconds must be a positive integer"


@pytest.mark.parametrize("seconds", [0, -1])
def test_store_expire_defensively_rejects_non_positive_seconds(seconds: int) -> None:
    store = InMemoryKVStore()
    store.set("user:expire:1", "kim")

    assert store.expire("user:expire:1", seconds) is False
    assert store.ttl("user:expire:1") == -1


def test_expire_endpoint_returns_ttl_invalid_for_zero_seconds() -> None:
    client = TestClient(app)

    response = client.post("/v1/kv/expire", json={"key": "user:ttl", "seconds": 0})

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error": {"code": "TTL_INVALID", "message": "seconds must be a positive integer"},
    }


def test_expire_endpoint_returns_false_for_missing_key() -> None:
    client = TestClient(app)

    response = client.post("/v1/kv/expire", json={"key": "user:missing", "seconds": 30})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"updated": False}}
