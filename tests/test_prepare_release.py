"""Tests for prepare_release and _next_version in release_notes."""
import json
import os
import subprocess

import pytest

from heat_simulation.release.release_notes import (
    _next_version,
    _collect_commits,
    prepare_release,
)


def _init_repo(tmp_path, with_tag=None):
    """Create a minimal git repo, optionally with a tag."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: initial commit"], cwd=str(tmp_path), capture_output=True)
    if with_tag:
        subprocess.run(["git", "tag", "-a", with_tag, "-m", f"Release {with_tag}"], cwd=str(tmp_path), capture_output=True)
        # Add a second commit after the tag
        (tmp_path / "file2.txt").write_text("world")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "fix: follow-up"], cwd=str(tmp_path), capture_output=True)


class TestNextVersion:
    def test_patch_bump(self, tmp_path):
        _init_repo(tmp_path, with_tag="v1.2.3")
        result = _next_version(str(tmp_path), "patch")
        assert result == "v1.2.4"

    def test_minor_bump(self, tmp_path):
        _init_repo(tmp_path, with_tag="v1.2.3")
        result = _next_version(str(tmp_path), "minor")
        assert result == "v1.3.0"

    def test_no_existing_tag(self, tmp_path):
        _init_repo(tmp_path)
        result = _next_version(str(tmp_path), "patch")
        assert result == "v0.0.1"

    def test_unsupported_bump_raises(self, tmp_path):
        _init_repo(tmp_path, with_tag="v1.0.0")
        with pytest.raises(RuntimeError, match="Unsupported bump"):
            _next_version(str(tmp_path), "major")


class TestCollectCommits:
    def test_collects_commits(self, tmp_path):
        _init_repo(tmp_path)
        commits = _collect_commits(str(tmp_path), "HEAD")
        assert len(commits) >= 1
        # first element is (hash, subject)
        assert len(commits[0]) == 2

    def test_with_tag_range(self, tmp_path):
        _init_repo(tmp_path, with_tag="v1.0.0")
        commits = _collect_commits(str(tmp_path), "v1.0.0..HEAD")
        assert len(commits) >= 1
        # The commit after the tag
        assert any("follow-up" in subject for _, subject in commits)


class TestPrepareRelease:
    def test_dry_run_does_not_modify_files(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        changelog_path = tmp_path / "CHANGELOG.md"
        changelog_existed = changelog_path.exists()

        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=False,
            dry_run=True,
        )

        # Changelog should not be created/modified in dry run
        assert changelog_path.exists() == changelog_existed

    def test_creates_changelog(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=False,
            dry_run=False,
        )
        changelog = (tmp_path / "CHANGELOG.md").read_text()
        assert "v0.2.0" in changelog

    def test_bump_mode(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        prepare_release(
            base_dir=str(tmp_path),
            version=None,
            create_tag=False,
            dry_run=False,
            bump="patch",
        )
        changelog = (tmp_path / "CHANGELOG.md").read_text()
        assert "v0.1.1" in changelog

    def test_version_and_bump_raises(self, tmp_path):
        _init_repo(tmp_path)
        with pytest.raises(RuntimeError, match="cannot be used together"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v1.0.0",
                create_tag=False,
                dry_run=True,
                bump="patch",
            )

    def test_from_tag_and_since_days_raises(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        with pytest.raises(RuntimeError, match="cannot be used together"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v0.2.0",
                create_tag=False,
                dry_run=True,
                from_tag="v0.1.0",
                since_days=7,
            )

    def test_since_days_negative_raises(self, tmp_path):
        _init_repo(tmp_path)
        with pytest.raises(RuntimeError, match="positive integer"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v1.0.0",
                create_tag=False,
                dry_run=True,
                since_days=-1,
            )

    def test_no_version_no_bump_raises(self, tmp_path):
        _init_repo(tmp_path)
        with pytest.raises(RuntimeError, match="Either --version or --bump"):
            prepare_release(
                base_dir=str(tmp_path),
                version=None,
                create_tag=False,
                dry_run=True,
            )

    def test_require_nonempty_with_no_commits(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        # Remove the extra commit by filtering with grep that won't match
        with pytest.raises(RuntimeError, match="No commits matched"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v0.2.0",
                create_tag=False,
                dry_run=True,
                require_nonempty=True,
                grep_text="ZZZZNONEXISTENTZZZZ",
            )

    def test_create_tag(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        prepare_release(
            base_dir=str(tmp_path),
            version="v0.2.0",
            create_tag=True,
            dry_run=False,
        )
        # Verify tag was created
        result = subprocess.run(
            ["git", "tag", "-l", "v0.2.0"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        assert "v0.2.0" in result.stdout

    def test_duplicate_tag_raises(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        with pytest.raises(RuntimeError, match="Tag already exists"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v0.1.0",
                create_tag=True,
                dry_run=False,
            )

    def test_output_json(self, tmp_path):
        _init_repo(tmp_path, with_tag="v0.1.0")
        json_path = str(tmp_path / "output" / "release.json")
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

    def test_from_tag_nonexistent_raises(self, tmp_path):
        _init_repo(tmp_path)
        with pytest.raises(RuntimeError, match="from-tag does not exist"):
            prepare_release(
                base_dir=str(tmp_path),
                version="v1.0.0",
                create_tag=False,
                dry_run=True,
                from_tag="v99.99.99",
            )

    def test_since_days(self, tmp_path):
        _init_repo(tmp_path)
        prepare_release(
            base_dir=str(tmp_path),
            version="v1.0.0",
            create_tag=False,
            dry_run=False,
            since_days=30,
        )
        changelog = (tmp_path / "CHANGELOG.md").read_text()
        assert "v1.0.0" in changelog
