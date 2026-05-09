import unittest
import os
import ast

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
ROOT_DIR = os.path.dirname(PROJECT_DIR)
DOCS_DIR = os.path.join(ROOT_DIR, "documents", "07_gestion_de_projet", "tasks")


def get_classes(fp):
    with open(fp) as f:
        tree = ast.parse(f.read())
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def get_functions(fp):
    with open(fp) as f:
        tree = ast.parse(f.read())
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


def has_text(fp, text):
    with open(fp) as f:
        return text in f.read()


class TestEPIC05_Correlation(unittest.TestCase):
    def test_models_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "correlation", "models.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("CorrelationGroup", classes)
        self.assertIn("CorrelatedEvent", classes)

    def test_schemas_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "correlation", "schemas.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("CorrelationGroupResponse", classes)
        self.assertIn("CorrelatedEventResponse", classes)
        self.assertIn("CorrelationSummary", classes)

    def test_service_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "correlation", "service.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("correlate_by_ip", funcs)
        self.assertIn("correlate_by_time_window", funcs)
        self.assertIn("get_correlation_groups", funcs)
        self.assertIn("get_group_by_id", funcs)
        self.assertIn("get_group_events", funcs)
        self.assertIn("resolve_group", funcs)
        self.assertIn("get_correlation_summary", funcs)

    def test_routes_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "correlation", "routes.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("list_correlations", funcs)
        self.assertIn("correlation_summary", funcs)
        self.assertIn("run_ip_correlation", funcs)
        self.assertIn("run_temporal_correlation", funcs)
        self.assertIn("resolve_correlation_group", funcs)

    def test_init_exports(self):
        fp = os.path.join(BACKEND_DIR, "app", "correlation", "__init__.py")
        self.assertTrue(has_text(fp, "router"))

    def test_correlation_model_fields(self):
        fp = os.path.join(BACKEND_DIR, "app", "correlation", "models.py")
        with open(fp) as f:
            content = f.read()
        self.assertIn("group_type", content)
        self.assertIn("source_ip", content)
        self.assertIn("is_resolved", content)
        self.assertIn("CorrelatedEvent", content)


class TestEPIC06_Dashboard(unittest.TestCase):
    def test_reports_schemas_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "reports", "schemas.py")
        self.assertTrue(os.path.exists(fp))
        classes = get_classes(fp)
        self.assertIn("DashboardSummary", classes)
        self.assertIn("AlertBreakdown", classes)
        self.assertIn("EventBreakdown", classes)
        self.assertIn("AssetBreakdown", classes)
        self.assertIn("ExportResponse", classes)

    def test_reports_service_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "reports", "service.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("get_dashboard_summary", funcs)
        self.assertIn("get_alert_breakdown", funcs)
        self.assertIn("get_event_breakdown", funcs)
        self.assertIn("get_asset_breakdown", funcs)
        self.assertIn("export_alerts_csv", funcs)
        self.assertIn("export_events_csv", funcs)
        self.assertIn("export_assets_csv", funcs)
        self.assertIn("export_json", funcs)

    def test_reports_routes_exist(self):
        fp = os.path.join(BACKEND_DIR, "app", "reports", "routes.py")
        self.assertTrue(os.path.exists(fp))
        funcs = get_functions(fp)
        self.assertIn("dashboard_summary", funcs)
        self.assertIn("alert_breakdown", funcs)
        self.assertIn("event_breakdown", funcs)
        self.assertIn("asset_breakdown", funcs)
        self.assertIn("export_alerts_to_csv", funcs)
        self.assertIn("export_events_to_csv", funcs)
        self.assertIn("export_assets_to_csv", funcs)
        self.assertIn("export_to_json", funcs)

    def test_init_exports(self):
        fp = os.path.join(BACKEND_DIR, "app", "reports", "__init__.py")
        self.assertTrue(has_text(fp, "router"))


class TestMainIntegration(unittest.TestCase):
    def test_main_registers_correlation(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        with open(fp) as f:
            content = f.read()
        self.assertIn("correlation_router", content)
        self.assertIn("/correlation", content)

    def test_main_registers_reports(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        with open(fp) as f:
            content = f.read()
        self.assertIn("reports_router", content)
        self.assertIn("/reports", content)

    def test_main_version_updated(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        with open(fp) as f:
            content = f.read()
        self.assertIn("0.5.0", content)

    def test_all_routers_registered(self):
        fp = os.path.join(BACKEND_DIR, "app", "main.py")
        with open(fp) as f:
            content = f.read()
        for prefix in ["/auth", "/telemetry", "/assets", "/alerts", "/correlation", "/reports"]:
            self.assertIn(prefix, content, f"Missing prefix: {prefix}")


class TestDocumentationSync(unittest.TestCase):
    def test_epic_05_updated(self):
        fp = os.path.join(DOCS_DIR, "EPIC-05-correlation.md")
        self.assertTrue(os.path.exists(fp))
        with open(fp) as f:
            content = f.read()
        self.assertGreater(content.count("- [x]"), 2)

    def test_epic_06_updated(self):
        fp = os.path.join(DOCS_DIR, "EPIC-06-interface-web.md")
        self.assertTrue(os.path.exists(fp))
        with open(fp) as f:
            content = f.read()
        self.assertGreater(content.count("- [x]"), 2)

    def test_sprint_4_in_backlog(self):
        fp = os.path.join(DOCS_DIR, "sprint-backlog.md")
        self.assertTrue(os.path.exists(fp))
        with open(fp) as f:
            content = f.read()
        self.assertIn("Sprint 4", content)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestEPIC05_Correlation))
    suite.addTests(loader.loadTestsFromTestCase(TestEPIC06_Dashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestMainIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentationSync))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n{'='*60}")
    print(f"SPRINT 4 TESTS: {result.testsRun} | Passed: {passed} | Failed: {len(result.failures)} | Errors: {len(result.errors)}")
    print(f"{'='*60}")
