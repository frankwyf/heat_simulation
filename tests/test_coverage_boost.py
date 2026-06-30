"""Additional coverage tests for release_notes and local_validation edge cases."""
import json
import os
import subprocess

import pytest

from heat_simulation.release.release_notes import (
    _collect_commits,
    _tag_exists,
    prepare_release,
)
from heat_simulation.validation.local_validation import _run


def _init_repo(tmp_path, with_tag=None):
    """Create a minimal git repo."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: initial commit"], cwd=str(tmp_path), capture_output=True)
    if with_tag:
        subprocess.run(["git", "tag", "-a", with_tag, "-m", f"Release {with_tag}"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / "file2.txt").write_text("world")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "fix: follow-up change"], cwd=str(tmp_path), capture_output=True)


class TestLocalValidationRun:
    """Cover the actual _run function (lines 12-19 of local_validation.py)."""

    def test_successful_command(self, tmp_path):
        # A simple command that always succeeds
        import sys
        result = _run([sys.executable, "-c", "print('hello world')"], str(tmp_path))
        assert "hello world" in result

    def test_failed_command_raises(self, tmp_path):
        import sys
        with pytest.raises(RuntimeError, match="Command failed"):
            _run([sys.executable, "-c", "import sys; sys.exit(1)"], str(tmp_path))


class TestCollectCommitsFilters:
    """Cover since_days, author, grep filters in _collect_commits."""

    def test_with_since_days(self, tmp_path):
        _init_repo(tmp_path)
        # All commits in last 30 days
        commits = _collect_commits(str(tmp_path), "HEAD", since_days=30)
        assert len(commits) >= 1

    def test_with_author_filter(self, tmp_path):
        _init_repo(tmp_path)
        commits = _collect_commits(str(tmp_path), "HEAD", author="T")
        assert len(commits) >= 1

    def test_with_grep_filter(self, tmp_path):
        _init_repo(tmp_path)
        commits = _collect_commits(str(tmp_path), "HEAD", grep_text="initial")
        assert len(commits) >= 1
        assert any("initial" in s for _, s in commits)

    def test_grep_no_match(self, tmp_path):
        _init_repo(tmp_path)
        commits = _collect_commits(str(tmp_path), "HEAD", grep_text="ZZZZZ_NO_MATCH")
        assert len(commits) == 0


class TestTagExists:
    def test_existing_tag(self, tmp_path):
        _init_repo(tmp_path, with_tag="v1.0.0")
        assert _tag_exists(str(tmp_path), "v1.0.0") is True

    def test_nonexistent_tag(self, tmp_path):
        _init_repo(tmp_path)
        assert _tag_exists(str(tmp_path), "v99.99.99") is False


class TestPrepareReleaseAdvanced:
    """Cover since_days path, output_json, from_tag not existing."""

    def test_since_days_path(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=False,
            dry_run=False,
            since_days=30,
        )
        changelog = (tmp_path / "CHANGELOG.md").read_text()
        assert "v0.2.0" in changelog

    def test_output_json_created(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        json_path = str(tmp_path / "release_output.json")
        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=False,
            dry_run=False,
            output_json=json_path,
        )
        assert os.path.exists(json_path)
        data = json.loads(open(json_path).read())
        assert data["version"] == "v0.2.0"
        assert "commits" in data
        assert data["dry_run"] is False

    def test_from_tag_not_existing_raises(self, tmp_path):
        _init_repo(tmp_path)
        with pytest.raises(RuntimeError, match="from-tag does not exist"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v1.0.0",
                create_tag=False,
                dry_run=True,
                from_tag="v_nonexistent",
            )

    def test_create_tag_already_exists_raises(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        with pytest.raises(RuntimeError, match="Tag already exists"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v0.1.0",
                create_tag=True,
                dry_run=False,
            )

    def test_author_filter_in_prepare(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=False,
            dry_run=False,
            author="T",
        )
        changelog = (tmp_path / "CHANGELOG.md").read_text()
        assert "v0.2.0" in changelog

    def test_grep_filter_in_prepare(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=False,
            dry_run=False,
            grep_text="follow-up",
        )
        changelog = (tmp_path / "CHANGELOG.md").read_text()
        assert "v0.2.0" in changelog
