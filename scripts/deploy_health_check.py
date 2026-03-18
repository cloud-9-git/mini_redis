from __future__ import annotations

import argparse
import sys
import time

import httpx


def is_healthy(url: str, request_timeout_sec: float = 2.0) -> bool:
    try:
        response = httpx.get(url, timeout=request_timeout_sec)
    except Exception:
        return False

    if response.status_code != 200:
        return False

    try:
        payload = response.json()
    except ValueError:
        return False

    return bool(payload.get("success") is True and payload.get("data", {}).get("status") == "ok")


def wait_for_health(
    url: str,
    max_attempts: int = 10,
    interval_sec: float = 3.0,
    request_timeout_sec: float = 2.0,
) -> bool:
    for _ in range(max_attempts):
        if is_healthy(url, request_timeout_sec=request_timeout_sec):
            return True
        time.sleep(interval_sec)
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deployment health check helper")
    parser.add_argument("--url", default="http://localhost:8000/v1/health")
    parser.add_argument("--attempts", type=int, default=10)
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=2.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ok = wait_for_health(
        url=args.url,
        max_attempts=args.attempts,
        interval_sec=args.interval,
        request_timeout_sec=args.timeout,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
