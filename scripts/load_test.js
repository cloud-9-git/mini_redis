import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 50,
  duration: "1m",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<300"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const setRes = http.post(
    `${BASE_URL}/v1/kv/set`,
    JSON.stringify({ key: "user:load", value: "benchmark" }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(setRes, { "set status is 200": (r) => r.status === 200 });

  const getRes = http.get(`${BASE_URL}/v1/kv/get?key=user:load`);
  check(getRes, { "get status is 200": (r) => r.status === 200 });

  const metricsRes = http.get(`${BASE_URL}/v1/metrics/cache`);
  check(metricsRes, { "metrics status is 200": (r) => r.status === 200 });

  sleep(0.2);
}
