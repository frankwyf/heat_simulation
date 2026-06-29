"""Tests for heat_simulation.validation.local_validation (main flow)."""
import json
import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from heat_simulation.validation.local_validation import main


class TestLocalValidationMain:
    """Integration-style tests for the validation main function.

    These test that main() runs the validation pipeline end-to-end
    in a controlled environment.
    """

    def test_main_runs_without_error(self, tmp_path, monkeypatch):
        """Integration test: main() should complete without raising."""
        # Create a minimal project structure that local_validation expects
        project = tmp_path / "project"
        project.mkdir()
        (project / "solve.py").write_text("import sys; print('ok')")
        (project / "app.py").write_text("print('app')")

        # Create the heat_simulation package structure
        pkg = project / "heat_simulation"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        core = pkg / "core"
        core.mkdir()
        (core / "__init__.py").write_text("")
        (core / "simulation_core.py").write_text("x = 1")
        bench = pkg / "benchmarks"
        bench.mkdir()
        (bench / "__init__.py").write_text("")
        (bench / "benchmark_suite.py").write_text("x = 1")
        (bench / "portfolio_report.py").write_text("x = 1")
        release = pkg / "release"
        release.mkdir()
        (release / "__init__.py").write_text("")
        (release / "release_notes.py").write_text("x = 1")
        (release / "publish_check.py").write_text("x = 1")

        reports = project / "reports"
        reports.mkdir()

        # Mock _run to succeed with expected outputs
        calls = []

        def fake_run(cmd, cwd):
            calls.append(cmd)
            if "benchmark" in " ".join(cmd):
                return "benchmark done"
            if "portfolio_report" in " ".join(cmd):
                return "report done"
            return ""

        with patch("heat_simulation.validation.local_validation._run", fake_run):
            with patch("heat_simulation.validation.local_validation.REPORTS_DIR", reports):
                main(str(project))

        # Check validation summary was created
        summary = reports / "validation_summary.json"
        assert summary.exists()
        data = json.loads(summary.read_text())
        assert data["status"] == "passed"
        assert "checks" in data
