#!/usr/bin/env python3
"""DevinciWatch - Sprint 3 Validation Tests (stdlib + AST)

Tests structure and coherence for:
- EPIC-03: Assets & Discovery
- EPIC-04: Alerts, Detection & Audit
"""

import unittest
import sys
import os
import ast

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
ROOT_DIR = os.path.dirname(PROJECT_DIR)
DOCS_DIR = os.path.join(ROOT_DIR, "documents", "07_gestion_de_projet", "tasks")


def parse_file(filepath):
    with open(filepath, "r") as f:
        return ast.parse(f.read())


def get_classes(filepath):
    tree = parse_file(filepath)
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def get_functions(filepath):
    tree = parse_file(filepath)
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def file_contains(filepath, text):
    return text in open(filepath).read()


class TestEPIC03_Assets(unittest.TestCase):
    def test_models_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "models.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("Asset", classes)
        self.assertIn("PortFinding", classes)

    def test_schemas_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "schemas.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("AssetCreate", classes)
        self.assertIn("AssetResponse", classes)
        self.assertIn("PortFindingResponse", classes)
        self.assertIn("ScanRequest", classes)
        self.assertIn("ScanResult", classes)

    def test_service_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "service.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("create_or_update_asset", funcs)
        self.assertIn("discover_network", funcs)
        self.assertIn("get_assets", funcs)
        self.assertIn("get_asset_by_id", funcs)
        self.assertIn("get_asset_ports", funcs)
        self.assertIn("add_port_finding", funcs)

    def test_routes_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "routes.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("list_assets", funcs)
        self.assertIn("create_asset", funcs)
        self.assertIn("scan_network", funcs)
        self.assertIn("get_asset", funcs)
        self.assertIn("get_asset_ports_route", funcs)

    def test_init_exports(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "__init__.py")
        self.assertTrue(file_contains(fp, "router"))

    def test_asset_model_fields(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "models.py")
        content = open(fp).read()
        self.assertIn("ip_address", content)
        self.assertIn("hostname", content)
        self.assertIn("mac_address", content)
        self.assertIn("asset_type", content)
        self.assertIn("PortFinding", content)

    def test_port_finding_model_fields(self):
        fp = os.path.join(BACKEND_DIR, "app", "assets", "models.py")
        content = open(fp).read()
        self.assertIn("port", content)
        self.assertIn("protocol", content)
        self.assertIn("service", content)
        self.assertIn("version", content)


class TestEPIC03_Discovery(unittest.TestCase):
    def test_discovery_service_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "discovery", "service.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("discover_single_host", funcs)
        self.assertIn("discover_network_range", funcs)
        self.assertIn("scan_ports", funcs)
        self.assertIn("ping_host", funcs)

    def test_discovery_init_exports(self):
        fp = os.path.join(BACKEND_DIR, "app", "discovery", "__init__.py")
        self.assertTrue(os.path.exists(fp))


class TestEPIC04_Alerts(unittest.TestCase):
    def test_models_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "models.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("Alert", classes)
        self.assertIn("AuditLog", classes)

    def test_schemas_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "schemas.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("AlertResponse", classes)
        self.assertIn("AlertUpdateStatus", classes)
        self.assertIn("AuditLogResponse", classes)

    def test_service_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "service.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("create_alert", funcs)
        self.assertIn("update_alert_status", funcs)
        self.assertIn("get_alerts", funcs)
        self.assertIn("evaluate_detection_rules", funcs)
        self.assertIn("log_audit", funcs)
        self.assertIn("get_audit_logs", funcs)

    def test_routes_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "routes.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("list_alerts", funcs)
        self.assertIn("create_alert_route", funcs)
        self.assertIn("update_alert_status_route", funcs)
        self.assertIn("run_detection", funcs)
        self.assertIn("list_audit_logs", funcs)

    def test_init_exports(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "__init__.py")
        self.assertTrue(file_contains(fp, "router"))

    def test_alert_model_fields(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "models.py")
        content = open(fp).read()
        self.assertIn("title", content)
        self.assertIn("severity", content)
        self.assertIn("status", content)
        self.assertIn("source_ip", content)
        self.assertIn("rule_name", content)

    def test_audit_log_model_fields(self):
        fp = os.path.join(BACKEND_DIR, "app", "alerts", "models.py")
        content = open(fp).read()
        self.assertIn("action", content)
        self.assertIn("actor", content)
        self.assertIn("target_type", content)
        self.assertIn("details", content)


class TestMainIntegration(unittest.TestCase):
    def test_main_registers_assets(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        content = open(fp).read()
        self.assertIn("assets_router", content)
        self.assertIn("/assets", content)

    def test_main_registers_alerts(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        content = open(fp).read()
        self.assertIn("alerts_router", content)
        self.assertIn("/alerts", content)

    def test_main_registers_telemetry(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        content = open(fp).read()
        self.assertIn("telemetry_router", content)
        self.assertIn("/telemetry", content)

    def test_main_registers_auth(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        content = open(fp).read()
        self.assertIn("auth_router", content)
        self.assertIn("/auth", content)


class TestDocumentationSync(unittest.TestCase):
    def test_epic_03_updated(self):
        fp = os.path.join(DOCS_DIR, "EPIC-03-decouverte-actifs.md")
        self.assertTrue(os.path.exists(fp))
        content = open(fp).read()
        self.assertGreater(content.count("- [x]"), 2)

    def test_epic_04_updated(self):
        fp = os.path.join(DOCS_DIR, "EPIC-04-detection-alertes.md")
        self.assertTrue(os.path.exists(fp))
        content = open(fp).read()
        self.assertGreater(content.count("- [x]"), 2)

    def test_sprint_3_in_backlog(self):
        fp = os.path.join(DOCS_DIR, "sprint-backlog.md")
        self.assertTrue(os.path.exists(fp))
        content = open(fp).read()
        self.assertIn("Sprint 3", content)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestEPIC03_Assets))
    suite.addTests(loader.loadTestsFromTestCase(TestEPIC03_Discovery))
    suite.addTests(loader.loadTestsFromTestCase(TestEPIC04_Alerts))
    suite.addTests(loader.loadTestsFromTestCase(TestMainIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentationSync))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n{'='*60}")
    print(f"SPRINT 3 TESTS: {result.testsRun} | Passed: {passed} | Failed: {len(result.failures)} | Errors: {len(result.errors)}")
    print(f"{'='*60}")

    sys.exit(0 if result.wasSuccessful() else 1)
