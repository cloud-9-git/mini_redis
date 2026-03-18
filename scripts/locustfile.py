"""
Locust load-test template for Stage-4 part1.

Run example:
  locust -f scripts/locustfile.py --headless -u 50 -r 10 -t 1m --host http://localhost:8000
"""

from __future__ import annotations

from locust import HttpUser
from locust import between
from locust import task


class MiniRedisLoadUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def get_existing_key(self) -> None:
        self.client.get("/v1/kv/get", params={"key": "user:load"})

    @task(1)
    def set_key(self) -> None:
        self.client.post("/v1/kv/set", json={"key": "user:load", "value": "benchmark"})

    @task(1)
    def ttl_key(self) -> None:
        self.client.get("/v1/kv/ttl", params={"key": "user:load"})

    @task(1)
    def metrics(self) -> None:
        self.client.get("/v1/metrics/cache")
