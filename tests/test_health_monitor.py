"""Tests for heat_simulation.analysis.health_monitor."""
import json
import os
from unittest.mock import patch, MagicMock

import pytest

from heat_simulation.analysis.health_monitor import (
    HealthCheck,
    SystemHealthReport,
    check_python_version,
    check_numpy_available,
    check_scipy_available,
    check_reports_directory,
    check_simulation_import,
    check_disk_space,
    run_health_checks,
    format_health_markdown,
)


class TestHealthCheck:
    def test_create_health_check(self):
        hc = HealthCheck(name="test", status="ok", message="all good", elapsed_ms=1.5)
        assert hc.name == "test"
        assert hc.status == "ok"
        assert hc.message == "all good"
        assert hc.elapsed_ms == pytest.approx(1.5)


class TestSystemHealthReport:
    def test_to_dict(self):
        report = SystemHealthReport(
            timestamp="2025-01-01T00:00:00",
            python_version="3.12.0",
            platform_info="Windows-10",
            workspace_path="/tmp",
            overall_status="healthy",
            summary="6/6 ok",
        )
        d = report.to_dict()
        assert d["overall_status"] == "healthy"
        assert d["python_version"] == "3.12.0"
        assert isinstance(d["checks"], list)


class TestCheckPythonVersion:
    def test_current_version_ok(self):
        result = check_python_version(min_version=(3, 10))
        assert result.status == "ok"
        assert result.name == "python_version"
        assert result.elapsed_ms >= 0

    def test_high_requirement_fails(self):
        result = check_python_version(min_version=(99, 99))
        assert result.status == "fail"
        assert "99" in result.message


class TestCheckNumpyAvailable:
    def test_numpy_ok(self):
        result = check_numpy_available()
        assert result.status == "ok"
        assert "numpy" in result.message


class TestCheckScipyAvailable:
    def test_scipy_ok(self):
        result = check_scipy_available()
        assert result.status == "ok"
        assert "scipy" in result.message


class TestCheckReportsDirectory:
    def test_writable_dir(self, tmp_path):
        workspace = str(tmp_path)
        result = check_reports_directory(workspace)
        assert result.status == "ok"
        assert "writable" in result.message
        # Probe file should be cleaned up
        probe = tmp_path / "reports" / ".health_check_probe"
        assert not probe.exists()

    def test_reports_dir_created(self, tmp_path):
        workspace = str(tmp_path / "nested" / "deep")
        result = check_reports_directory(workspace)
        assert result.status == "ok"


class TestCheckSimulationImport:
    def test_import_ok(self):
        result = check_simulation_import()
        assert result.status == "ok"
        assert "simulation_core" in result.message


class TestCheckDiskSpace:
    def test_sufficient_space(self, tmp_path):
        result = check_disk_space(str(tmp_path), min_mb=1.0)
        # Should pass unless disk is literally full
        assert result.status in ("ok", "warn")

    def test_unrealistic_requirement_warns(self, tmp_path):
        # 100 TB requirement should warn
        result = check_disk_space(str(tmp_path), min_mb=100_000_000)
        assert result.status == "warn"
        assert "Only" in result.message


class TestRunHealthChecks:
    def test_full_run(self, tmp_path):
        report = run_health_checks(str(tmp_path))
        assert report.overall_status in ("healthy", "degraded", "unhealthy")
        assert len(report.checks) == 6
        assert report.python_version != ""
        assert report.timestamp != ""

    def test_healthy_workspace(self, tmp_path):
        report = run_health_checks(str(tmp_path))
        # With all deps installed, should be healthy
        assert report.overall_status == "healthy"
        assert "6/6" in report.summary

    def test_report_contains_all_check_names(self, tmp_path):
        report = run_health_checks(str(tmp_path))
        names = [c.name for c in report.checks]
        assert "python_version" in names
        assert "numpy" in names
        assert "scipy" in names
        assert "reports_dir" in names
        assert "simulation_core" in names
        assert "disk_space" in names


class TestFormatHealthMarkdown:
    def test_markdown_structure(self, tmp_path):
        report = run_health_checks(str(tmp_path))
        md = format_health_markdown(report)
        assert "# System Health Report" in md
        assert "## Checks" in md
        assert "| Check |" in md
        assert report.overall_status in md

    def test_contains_check_results(self, tmp_path):
        report = run_health_checks(str(tmp_path))
        md = format_health_markdown(report)
        assert "python_version" in md
        assert "numpy" in md
        assert "✓" in md  # At least some OK checks

    def test_summary_line(self, tmp_path):
        report = run_health_checks(str(tmp_path))
        md = format_health_markdown(report)
        assert "**Summary**" in md


class TestHealthChecksExceptionBranches:
    """Cover exception/failure branches in health checks via mocking."""

    def test_numpy_fail(self):
        with patch("heat_simulation.analysis.health_monitor.np") as mock_np:
            mock_np.array.side_effect = RuntimeError("numpy broken")
            result = check_numpy_available()
            assert result.status == "fail"
            assert "numpy broken" in result.message

    def test_scipy_import_fail(self):
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "scipy":
                raise ImportError("no scipy")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            result = check_scipy_available()
            assert result.status == "fail"
            assert "no scipy" in result.message

    def test_reports_dir_fail(self, tmp_path):
        # Use a path that can't be written to
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("denied")):
            result = check_reports_directory(str(tmp_path))
            assert result.status == "fail"
            assert "denied" in result.message

    def test_simulation_import_fail(self):
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if "simulation_core" in name:
                raise ImportError("missing module")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            result = check_simulation_import()
            assert result.status == "fail"

    def test_disk_space_exception(self, tmp_path):
        with patch("shutil.disk_usage", side_effect=OSError("disk error")):
            result = check_disk_space(str(tmp_path))
            assert result.status == "fail"
            assert "disk error" in result.message

    def test_overall_unhealthy_with_fail(self, tmp_path):
        """When a check fails, overall status should be unhealthy."""
        with patch("heat_simulation.analysis.health_monitor.check_numpy_available") as mock:
            mock.return_value = HealthCheck(name="numpy", status="fail", message="broken", elapsed_ms=0)
            report = run_health_checks(str(tmp_path))
            assert report.overall_status == "unhealthy"

    def test_overall_degraded_with_warn(self, tmp_path):
        """When a check warns, overall status should be degraded."""
        with patch("heat_simulation.analysis.health_monitor.check_disk_space") as mock:
            mock.return_value = HealthCheck(name="disk_space", status="warn", message="low", elapsed_ms=0)
            report = run_health_checks(str(tmp_path))
            assert report.overall_status == "degraded"
