from __future__ import annotations

from typing import Any

import httpx

from scripts import deploy_health_check


class DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


def test_is_healthy_true_when_status_and_payload_are_valid(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs) -> DummyResponse:
        return DummyResponse(200, {"success": True, "data": {"status": "ok"}})

    monkeypatch.setattr(httpx, "get", fake_get)

    assert deploy_health_check.is_healthy("http://localhost:8000/v1/health") is True


def test_wait_for_health_retries_until_success(monkeypatch) -> None:
    sequence = iter(
        [
            DummyResponse(500, {"success": False}),
            DummyResponse(200, {"success": True, "data": {"status": "ok"}}),
        ]
    )

    def fake_get(*_args, **_kwargs) -> DummyResponse:
        return next(sequence)

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(deploy_health_check.time, "sleep", lambda _x: None)

    assert deploy_health_check.wait_for_health(
        "http://localhost:8000/v1/health",
        max_attempts=3,
        interval_sec=0.01,
    ) is True


def test_wait_for_health_returns_false_after_max_attempts(monkeypatch) -> None:
    def fake_get(*_args, **_kwargs) -> DummyResponse:
        return DummyResponse(500, {"success": False})

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(deploy_health_check.time, "sleep", lambda _x: None)

    assert deploy_health_check.wait_for_health(
        "http://localhost:8000/v1/health",
        max_attempts=3,
        interval_sec=0.01,
    ) is False
