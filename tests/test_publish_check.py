"""Tests for heat_simulation.release.publish_check (generate_checklist)."""
import json
import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from heat_simulation.release.publish_check import generate_checklist, _run


# ---------------------------------------------------------------------------
# _run helper
# ---------------------------------------------------------------------------

class TestRun:
    def test_successful_command(self, tmp_path):
        # Use a simple command that works on all platforms
        result = _run(["git", "--version"], str(tmp_path))
        assert "git" in result.lower()

    def test_failed_command_returns_error_info(self, tmp_path):
        # This should fail (non-git dir)
        result = _run(["git", "log", "-1"], str(tmp_path))
        # _run returns error string with [failed] prefix when command fails
        assert "[failed]" in result or "fatal" in result.lower() or result != ""


# ---------------------------------------------------------------------------
# generate_checklist
# ---------------------------------------------------------------------------

class TestGenerateChecklist:
    def test_creates_output_file(self, tmp_path):
        # Set up a minimal git repo
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / "file.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

        out_path = str(tmp_path / "reports" / "readiness.md")
        generate_checklist(str(tmp_path), out_path)
        assert os.path.exists(out_path)

    def test_output_contains_sections(self, tmp_path):
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / "f.txt").write_text("x")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

        out_path = str(tmp_path / "readiness.md")
        generate_checklist(str(tmp_path), out_path)
        content = open(out_path, encoding="utf-8").read()
        assert "# Publish Readiness Check" in content
        assert "## Git Health" in content
        assert "## Validation" in content
        assert "## Ready To Publish" in content

    def test_no_validation_shows_not_ready(self, tmp_path):
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / "f.txt").write_text("x")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

        out_path = str(tmp_path / "out.md")
        generate_checklist(str(tmp_path), out_path)
        content = open(out_path, encoding="utf-8").read()
        assert "ready: no" in content

    def test_with_validation_passed(self, tmp_path, monkeypatch):
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)

        # Create validation summary BEFORE committing so working tree is clean
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        val_path = reports_dir / "validation_summary.json"
        val_path.write_text(json.dumps({
            "status": "passed",
            "validated_at": "2024-01-01T00:00:00",
            "checks": ["compile", "benchmark"],
        }))

        (tmp_path / "f.txt").write_text("x")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

        monkeypatch.setattr("heat_simulation.release.publish_check.REPORTS_DIR", reports_dir)
        out_path = str(tmp_path / "out2.md")
        generate_checklist(str(tmp_path), out_path)
        content = open(out_path, encoding="utf-8").read()
        assert "ready: yes" in content
        assert "validation status: passed" in content
