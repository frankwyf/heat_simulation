"""System Health Monitor for simulation infrastructure.

Provides diagnostic checks, resource usage summaries, and a status
dashboard suitable for industrial deployment monitoring.
"""
from __future__ import annotations

import os
import platform
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class HealthCheck:
    name: str
    status: str  # "ok", "warn", "fail"
    message: str
    elapsed_ms: float = 0.0


@dataclass
class SystemHealthReport:
    timestamp: str = ""
    python_version: str = ""
    platform_info: str = ""
    workspace_path: str = ""
    checks: List[HealthCheck] = field(default_factory=list)
    overall_status: str = "unknown"
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def check_python_version(min_version: tuple = (3, 10)) -> HealthCheck:
    """Verify Python version meets minimum requirement."""
    t0 = time.perf_counter()
    ver = sys.version_info[:2]
    elapsed = (time.perf_counter() - t0) * 1000

    if ver >= min_version:
        return HealthCheck(
            name="python_version",
            status="ok",
            message=f"Python {ver[0]}.{ver[1]} >= {min_version[0]}.{min_version[1]}",
            elapsed_ms=elapsed,
        )
    else:
        return HealthCheck(
            name="python_version",
            status="fail",
            message=f"Python {ver[0]}.{ver[1]} < required {min_version[0]}.{min_version[1]}",
            elapsed_ms=elapsed,
        )


def check_numpy_available() -> HealthCheck:
    """Check numpy is importable and functional."""
    t0 = time.perf_counter()
    try:
        arr = np.array([1.0, 2.0, 3.0])
        _ = np.mean(arr)
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(
            name="numpy",
            status="ok",
            message=f"numpy {np.__version__} operational",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(name="numpy", status="fail", message=str(e), elapsed_ms=elapsed)


def check_scipy_available() -> HealthCheck:
    """Check scipy is importable."""
    t0 = time.perf_counter()
    try:
        import scipy
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(
            name="scipy",
            status="ok",
            message=f"scipy {scipy.__version__} available",
            elapsed_ms=elapsed,
        )
    except ImportError as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(name="scipy", status="fail", message=str(e), elapsed_ms=elapsed)


def check_reports_directory(workspace: str) -> HealthCheck:
    """Verify reports directory is writable."""
    t0 = time.perf_counter()
    reports = Path(workspace) / "reports"
    try:
        reports.mkdir(parents=True, exist_ok=True)
        test_file = reports / ".health_check_probe"
        test_file.write_text("probe")
        test_file.unlink()
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(
            name="reports_dir",
            status="ok",
            message=f"{reports} writable",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(name="reports_dir", status="fail", message=str(e), elapsed_ms=elapsed)


def check_simulation_import() -> HealthCheck:
    """Verify core simulation module is importable."""
    t0 = time.perf_counter()
    try:
        from heat_simulation.core.simulation_core import run_heat_simulation, SimulationConfig
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(
            name="simulation_core",
            status="ok",
            message="simulation_core importable",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(name="simulation_core", status="fail", message=str(e), elapsed_ms=elapsed)


def check_disk_space(workspace: str, min_mb: float = 100.0) -> HealthCheck:
    """Check available disk space at workspace path."""
    t0 = time.perf_counter()
    try:
        import shutil
        usage = shutil.disk_usage(workspace)
        free_mb = usage.free / (1024 * 1024)
        elapsed = (time.perf_counter() - t0) * 1000
        if free_mb >= min_mb:
            return HealthCheck(
                name="disk_space",
                status="ok",
                message=f"{free_mb:.0f} MB free >= {min_mb:.0f} MB required",
                elapsed_ms=elapsed,
            )
        else:
            return HealthCheck(
                name="disk_space",
                status="warn",
                message=f"Only {free_mb:.0f} MB free (minimum {min_mb:.0f} MB)",
                elapsed_ms=elapsed,
            )
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return HealthCheck(name="disk_space", status="fail", message=str(e), elapsed_ms=elapsed)


def run_health_checks(workspace: str) -> SystemHealthReport:
    """Run all health checks and build a summary report."""
    report = SystemHealthReport(
        timestamp=datetime.now().isoformat(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform_info=platform.platform(),
        workspace_path=workspace,
    )

    report.checks = [
        check_python_version(),
        check_numpy_available(),
        check_scipy_available(),
        check_reports_directory(workspace),
        check_simulation_import(),
        check_disk_space(workspace),
    ]

    # Determine overall status
    statuses = [c.status for c in report.checks]
    if "fail" in statuses:
        report.overall_status = "unhealthy"
    elif "warn" in statuses:
        report.overall_status = "degraded"
    else:
        report.overall_status = "healthy"

    passed = sum(1 for s in statuses if s == "ok")
    total = len(statuses)
    report.summary = f"{passed}/{total} checks passed. Status: {report.overall_status}"

    return report


def format_health_markdown(report: SystemHealthReport) -> str:
    """Format health report as markdown for dashboards."""
    lines = [
        "# System Health Report",
        "",
        f"- Timestamp: {report.timestamp}",
        f"- Python: {report.python_version}",
        f"- Platform: {report.platform_info}",
        f"- Workspace: {report.workspace_path}",
        f"- Overall: **{report.overall_status}**",
        "",
        "## Checks",
        "",
        "| Check | Status | Message | Time (ms) |",
        "| ----- | ------ | ------- | --------- |",
    ]
    for c in report.checks:
        icon = {"ok": "✓", "warn": "⚠", "fail": "✗"}.get(c.status, "?")
        lines.append(f"| {c.name} | {icon} {c.status} | {c.message} | {c.elapsed_ms:.1f} |")

    lines.append("")
    lines.append(f"**Summary**: {report.summary}")
    return "\n".join(lines)
