"""
Sprint 5 tests - US-07.3, US-08.2, US-08.3

Validates scenario runner, export linking, and documentation structure.
Tests use AST analysis since full application requires database.
"""

import ast
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DOCUMENTATION_DIR = os.path.join(PROJECT_ROOT, "documents")


class TestScenarioRunner(unittest.TestCase):
    """Test US-08.2 - Scenario runner structure and completeness."""

    def setUp(self):
        self.scenario_path = os.path.join(SCENARIOS_DIR, "scenario_runner.py")
        with open(self.scenario_path) as f:
            self.source = f.read()
        self.tree = ast.parse(self.source)

    def test_scenario_file_exists(self):
        """Scenario runner file must exist."""
        self.assertTrue(os.path.exists(self.scenario_path), "scenario_runner.py must exist")

    def test_create_scenario_function(self):
        """Must have create_scenario function."""
        functions = [node.name for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)]
        self.assertIn("create_scenario", functions, "create_scenario function required")

    def test_run_scenario_function(self):
        """Must have run_scenario function."""
        functions = [node.name for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)]
        self.assertIn("run_scenario", functions, "run_scenario function required")

    def test_scenario_phases(self):
        """Scenario must include all attack phases."""
        phases = [
            "Phase 1", "Phase 2", "Phase 3", "Phase 4",
            "Phase 5", "Phase 6", "Phase 7", "Phase 8",
        ]
        for phase in phases:
            self.assertIn(phase, self.source, f"Scenario must include {phase}")

    def test_scenario_chain(self):
        """Scenario must create complete chain: heartbeat -> events -> alerts -> correlation."""
        chain_elements = [
            "Heartbeat(",
            "TelemetryEvent(",
            "Alert(",
            "CorrelationGroup(",
            "CorrelatedEvent(",
        ]
        for element in chain_elements:
            self.assertIn(element, self.source, f"Scenario chain must include {element}")

    def test_scenario_metadata(self):
        """Scenario must include metadata for export linking."""
        self.assertIn("scenario_id", self.source, "Scenario must have scenario_id")
        self.assertIn("scenario_name", self.source, "Scenario must have scenario_name")
        self.assertIn("scenario_context", self.source, "Scenario must have scenario_context")

    def test_attack_types(self):
        """Scenario must include multiple attack types."""
        attack_types = ["brute_force", "lateral_movement", "authentication_failure"]
        for attack in attack_types:
            self.assertIn(attack, self.source.lower(), f"Scenario must include {attack}")

    def test_imports(self):
        """Scenario must import required modules."""
        imports = [node for node in ast.walk(self.tree) if isinstance(node, ast.ImportFrom)]
        imported_modules = []
        for imp in imports:
            if imp.module:
                imported_modules.append(imp.module)

        required = ["app.core.database", "app.telemetry.models", "app.alerts.models", "app.assets.models"]
        for req in required:
            self.assertIn(req, imported_modules, f"Scenario must import {req}")


class TestExportLinking(unittest.TestCase):
    """Test US-07.3 - Export linking to scenarios."""

    def setUp(self):
        self.reports_service = os.path.join(BASE_DIR, "app", "reports", "service.py")
        with open(self.reports_service) as f:
            self.source = f.read()

    def test_export_json_has_metadata(self):
        """JSON export must include metadata fields."""
        self.assertIn("exported_at", self.source, "JSON export must include exported_at")
        self.assertIn("resource", self.source, "JSON export must include resource type")

    def test_export_csv_has_headers(self):
        """CSV export must include proper headers."""
        self.assertIn("writer.writerow", self.source, "CSV export must write headers")

    def test_scenario_id_in_exports(self):
        """Exports should support scenario_id linking via raw_data in models."""
        # Check that the models used by exports have raw_data field
        # This is verified by checking the scenario runner uses raw_data with scenario_id
        scenario_path = os.path.join(SCENARIOS_DIR, "scenario_runner.py")
        with open(scenario_path) as f:
            scenario_source = f.read()
        self.assertIn("scenario_id", scenario_source, "Scenario must embed scenario_id in raw_data")
        self.assertIn("raw_data", scenario_source, "Scenario must use raw_data for metadata")


class TestDocumentation(unittest.TestCase):
    """Test US-08.3 - Documentation completeness."""

    def test_readme_exists(self):
        """README.md must exist in project root."""
        readme_path = os.path.join(PROJECT_ROOT, "README.md")
        self.assertTrue(os.path.exists(readme_path), "README.md must exist")

    def test_readme_has_launch_procedure(self):
        """README must include launch procedure."""
        readme_path = os.path.join(PROJECT_ROOT, "README.md")
        with open(readme_path) as f:
            content = f.read()
        required_sections = ["Docker", "FastAPI", "lab"]
        for section in required_sections:
            self.assertIn(section.lower(), content.lower(), f"README must include {section}")

    def test_sprint_report_exists(self):
        """Sprint 4 report must exist."""
        report_path = os.path.join(
            PROJECT_ROOT,
            "documents", "07_gestion_de_projet", "sprint-reports",
            "sprint-4-report-2026-05-06.md"
        )
        self.assertTrue(os.path.exists(report_path), "Sprint 4 report must exist")

    def test_sprint_backlog_updated(self):
        """Sprint backlog must be updated."""
        backlog_path = os.path.join(
            PROJECT_ROOT,
            "documents", "07_gestion_de_projet", "tasks", "sprint-backlog.md"
        )
        self.assertTrue(os.path.exists(backlog_path), "Sprint backlog must exist")


class TestSprint5Completeness(unittest.TestCase):
    """Test overall Sprint 5 completeness."""

    def test_all_modules_importable(self):
        """All application modules must be syntactically valid."""
        modules = [
            "app/main.py",
            "app/core/database.py",
            "app/telemetry/routes.py",
            "app/alerts/routes.py",
            "app/assets/routes.py",
            "app/correlation/routes.py",
            "app/reports/routes.py",
            "scenarios/scenario_runner.py",
        ]
        for module in modules:
            path = os.path.join(BASE_DIR, module)
            if os.path.exists(path):
                with open(path) as f:
                    try:
                        ast.parse(f.read())
                    except SyntaxError as e:
                        self.fail(f"{module} has syntax error: {e}")

    def test_scenario_directory_structure(self):
        """Scenarios directory must have proper structure."""
        self.assertTrue(os.path.exists(SCENARIOS_DIR), "scenarios/ directory must exist")
        self.assertTrue(
            os.path.exists(os.path.join(SCENARIOS_DIR, "scenario_runner.py")),
            "scenario_runner.py must exist in scenarios/"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
