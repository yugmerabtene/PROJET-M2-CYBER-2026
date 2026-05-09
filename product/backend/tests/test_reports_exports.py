import csv
import io
import json
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import URLError


BASE_URL = "http://localhost:8000"


def http_json(method: str, path: str, token: str | None = None, body: dict | None = None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(f"{BASE_URL}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=20) as resp:  # nosec B310
        return resp.status, dict(resp.headers), json.loads(resp.read().decode("utf-8"))


def http_text(method: str, path: str, token: str | None = None):
    req = Request(f"{BASE_URL}{path}", method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=20) as resp:  # nosec B310
        return resp.status, dict(resp.headers), resp.read().decode("latin-1")


def wait_for_service(timeout: int = 30):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            req = Request(f"{BASE_URL}/health", method="GET")
            with urlopen(req, timeout=5) as resp:  # nosec B310
                if resp.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1)
    raise AssertionError(f"Service not ready after {timeout}s: {last_error}")


class ReportsExportsLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wait_for_service()
        status, _, payload = http_json(
            "POST",
            "/auth/login",
            body={"username": "admin", "password": "password"},
        )
        assert status == 200, payload
        cls.token = payload["access_token"]

    def test_dashboard_endpoint(self):
        status, _, payload = http_json("GET", "/reports/dashboard", token=self.token)
        self.assertEqual(status, 200)
        for key in [
            "total_events",
            "total_alerts",
            "total_assets",
            "total_agents",
            "active_alerts",
            "critical_alerts",
            "high_alerts",
            "generated_at",
        ]:
            self.assertIn(key, payload)

    def test_breakdown_endpoints(self):
        for path, required_keys in [
            ("/reports/dashboard/alerts", ["new", "acknowledged", "investigating", "resolved", "false_positive", "closed"]),
            ("/reports/dashboard/events", ["by_type", "by_severity", "last_24h"]),
            ("/reports/dashboard/assets", ["total", "active", "inactive", "by_type"]),
        ]:
            status, _, payload = http_json("GET", path, token=self.token)
            self.assertEqual(status, 200, path)
            for key in required_keys:
                self.assertIn(key, payload, path)

    def test_alerts_csv_export(self):
        status, headers, content = http_text("GET", "/reports/export/alerts/csv", token=self.token)
        self.assertEqual(status, 200)
        self.assertIn("text/csv", headers.get("Content-Type", headers.get("content-type", "")))
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(rows[0], ["id", "title", "severity", "status", "source_ip", "target_ip", "rule_name", "created_at"])
        self.assertGreaterEqual(len(rows), 1)

    def test_events_csv_export(self):
        status, _, content = http_text("GET", "/reports/export/events/csv", token=self.token)
        self.assertEqual(status, 200)
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(rows[0], ["id", "agent_id", "source_ip", "target_ip", "event_type", "severity", "message", "observed_at"])
        self.assertGreaterEqual(len(rows), 2)

    def test_assets_csv_export(self):
        status, _, content = http_text("GET", "/reports/export/assets/csv", token=self.token)
        self.assertEqual(status, 200)
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(rows[0], ["id", "ip_address", "hostname", "asset_type", "os_guess", "is_active", "last_seen"])
        self.assertGreaterEqual(len(rows), 1)

    def test_correlations_csv_export(self):
        status, _, content = http_text("GET", "/reports/export/correlations/csv", token=self.token)
        self.assertEqual(status, 200)
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(rows[0], ["id", "name", "group_type", "source_ip", "target_ip", "severity", "event_count", "correlation_score", "is_resolved", "created_at"])
        self.assertGreaterEqual(len(rows), 1)

    def test_alerts_json_export(self):
        status, _, payload = http_json("GET", "/reports/export/alerts/json", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["resource"], "alerts")
        self.assertIn("count", payload)
        self.assertIn("exported_at", payload)
        self.assertIn("data", payload)

    def test_events_json_export(self):
        status, _, payload = http_json("GET", "/reports/export/events/json", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["resource"], "events")
        self.assertIn("count", payload)
        self.assertIn("exported_at", payload)
        self.assertIn("data", payload)

    def test_assets_json_export(self):
        status, _, payload = http_json("GET", "/reports/export/assets/json", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["resource"], "assets")
        self.assertIn("count", payload)
        self.assertIn("exported_at", payload)
        self.assertIn("data", payload)

    def test_correlations_json_export(self):
        status, _, payload = http_json("GET", "/reports/export/correlations/json", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["resource"], "correlations")
        self.assertIn("count", payload)
        self.assertIn("exported_at", payload)
        self.assertIn("data", payload)

    def test_pdf_exports(self):
        for path in [
            "/reports/export/alerts/pdf",
            "/reports/export/events/pdf",
            "/reports/export/assets/pdf",
            "/reports/export/correlations/pdf",
        ]:
            status, headers, content = http_text("GET", path, token=self.token)
            self.assertEqual(status, 200)
            self.assertIn("application/pdf", headers.get("Content-Type", headers.get("content-type", "")))
            self.assertTrue(content.startswith("%PDF"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
