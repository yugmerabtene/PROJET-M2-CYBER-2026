#!/usr/bin/env python3
"""DevinciWatch - Tests de validation (stdlib uniquement)

Valide la structure du backend sans dépendances externes.
"""

import unittest
import sys
import os
import ast

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
ROOT_DIR = os.path.dirname(PROJECT_DIR)
DOCS_DIR = os.path.join(ROOT_DIR, "documents", "07_gestion_de_projet", "tasks")


def parse_python_file(filepath):
    with open(filepath, "r") as f:
        return ast.parse(f.read())


def get_imports(filepath):
    tree = parse_python_file(filepath)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    return imports


def get_classes(filepath):
    tree = parse_python_file(filepath)
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return classes


def get_functions(filepath):
    tree = parse_python_file(filepath)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    return functions


class TestBackendStructure(unittest.TestCase):
    def test_telemetry_models_exist(self):
        filepath = os.path.join(BACKEND_DIR, "app", "telemetry", "models.py")
        self.assertTrue(os.path.exists(filepath), f"Missing: {filepath}")
        classes = get_classes(filepath)
        self.assertIn("Agent", classes)
        self.assertIn("Heartbeat", classes)
        self.assertIn("TelemetryEvent", classes)

    def test_telemetry_schemas_exist(self):
        filepath = os.path.join(BACKEND_DIR, "app", "telemetry", "schemas.py")
        self.assertTrue(os.path.exists(filepath))
        classes = get_classes(filepath)
        self.assertIn("HeartbeatPayload", classes)
        self.assertIn("EventPayload", classes)
        self.assertIn("HeartbeatResponse", classes)
        self.assertIn("TelemetryEventResponse", classes)
        self.assertIn("AgentResponse", classes)

    def test_telemetry_service_exist(self):
        filepath = os.path.join(BACKEND_DIR, "app", "telemetry", "service.py")
        self.assertTrue(os.path.exists(filepath))
        functions = get_functions(filepath)
        self.assertIn("get_or_create_agent", functions)
        self.assertIn("record_heartbeat", functions)
        self.assertIn("record_event", functions)
        self.assertIn("get_latest_heartbeat", functions)
        self.assertIn("get_events", functions)
        self.assertIn("get_agents", functions)

    def test_telemetry_routes_exist(self):
        filepath = os.path.join(BACKEND_DIR, "app", "telemetry", "routes.py")
        self.assertTrue(os.path.exists(filepath))
        functions = get_functions(filepath)
        self.assertIn("ingest_heartbeat", functions)
        self.assertIn("ingest_event", functions)
        self.assertIn("get_last_heartbeat", functions)
        self.assertIn("list_events", functions)
        self.assertIn("list_agents", functions)

    def test_main_includes_telemetry_router(self):
        filepath = os.path.join(BACKEND_DIR, "app", "main.py")
        content = open(filepath).read()
        self.assertIn("telemetry_router", content)
        self.assertIn("/telemetry", content)

    def test_auth_models_exist(self):
        filepath = os.path.join(BACKEND_DIR, "app", "auth", "models.py")
        self.assertTrue(os.path.exists(filepath))
        classes = get_classes(filepath)
        self.assertIn("User", classes)

    def test_auth_routes_exist(self):
        filepath = os.path.join(BACKEND_DIR, "app", "auth", "routes.py")
        self.assertTrue(os.path.exists(filepath))
        functions = get_functions(filepath)
        self.assertIn("login", functions)
        self.assertIn("me", functions)

    def test_core_config_exists(self):
        filepath = os.path.join(BACKEND_DIR, "app", "core", "config.py")
        self.assertTrue(os.path.exists(filepath))
        classes = get_classes(filepath)
        self.assertIn("Settings", classes)

    def test_core_security_exists(self):
        filepath = os.path.join(BACKEND_DIR, "app", "core", "security.py")
        self.assertTrue(os.path.exists(filepath))
        functions = get_functions(filepath)
        self.assertIn("hash_password", functions)
        self.assertIn("verify_password", functions)
        self.assertIn("create_access_token", functions)
        self.assertIn("decode_token", functions)

    def test_core_deps_exists(self):
        filepath = os.path.join(BACKEND_DIR, "app", "core", "deps.py")
        self.assertTrue(os.path.exists(filepath))
        functions = get_functions(filepath)
        self.assertIn("get_db", functions)
        self.assertIn("get_current_user", functions)
        self.assertIn("require_admin", functions)
        self.assertIn("require_agent", functions)


class TestTelemetrySchemasStructure(unittest.TestCase):
    def test_heartbeat_payload_fields(self):
        filepath = os.path.join(BACKEND_DIR, "app", "telemetry", "schemas.py")
        self.assertTrue(os.path.exists(filepath))
        content = open(filepath).read()
        self.assertIn("agent_id", content)
        self.assertIn("hostname", content)
        self.assertIn("sent_at", content)
        self.assertIn("HeartbeatPayload", content)

    def test_event_payload_fields(self):
        filepath = os.path.join(BACKEND_DIR, "app", "telemetry", "schemas.py")
        content = open(filepath).read()
        self.assertIn("event_type", content)
        self.assertIn("severity", content)
        self.assertIn("source_ip", content)
        self.assertIn("target_ip", content)
        self.assertIn("EventPayload", content)


class TestDocumentationSync(unittest.TestCase):
    def test_epic_02_status_updated(self):
        epic_path = os.path.join(DOCS_DIR, "EPIC-02-collection-endpoint.md")
        self.assertTrue(os.path.exists(epic_path), f"Missing: {epic_path}")
        content = open(epic_path).read()
        self.assertIn("In Review", content)
        tasks_done = content.count("- [x]")
        self.assertGreater(tasks_done, 3, "EPIC-02 doit avoir au moins 4 tâches terminées")

    def test_sprint_backlog_updated(self):
        backlog_path = os.path.join(DOCS_DIR, "sprint-backlog.md")
        self.assertTrue(os.path.exists(backlog_path), f"Missing: {backlog_path}")
        content = open(backlog_path).read()
        self.assertIn("Sprint 2", content)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestBackendStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestTelemetrySchemasStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentationSync))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'='*60}")
    print(f"Tests: {result.testsRun} | Passed: {result.testsRun - len(result.failures) - len(result.errors)} | Failed: {len(result.failures)} | Errors: {len(result.errors)}")

    sys.exit(0 if result.wasSuccessful() else 1)
