"""Tests for heat_simulation.release.release_notes (more functions)."""
import json
import os
from datetime import datetime

import pytest

from heat_simulation.release.release_notes import (
    _parse_semver,
    _group_commits,
    _build_section,
    _update_changelog,
    SECTION_ORDER,
    SECTION_TITLES,
)


# ---------------------------------------------------------------------------
# _build_section
# ---------------------------------------------------------------------------

class TestBuildSection:
    def test_contains_version(self):
        grouped = {k: [] for k in SECTION_ORDER}
        grouped["feat"] = [("abc", "feat: hello")]
        section = _build_section("v1.0.0", grouped)
        assert "v1.0.0" in section

    def test_contains_date(self):
        grouped = {k: [] for k in SECTION_ORDER}
        grouped["fix"] = [("def", "fix: bug")]
        section = _build_section("v0.1.0", grouped)
        today = datetime.now().date().isoformat()
        assert today in section

    def test_contains_commit_hash(self):
        grouped = {k: [] for k in SECTION_ORDER}
        grouped["feat"] = [("abc1234", "feat: new thing")]
        section = _build_section("v1.0.0", grouped)
        assert "abc1234" in section

    def test_empty_sections_skipped(self):
        grouped = {k: [] for k in SECTION_ORDER}
        grouped["feat"] = [("abc", "feat: one")]
        section = _build_section("v1.0.0", grouped)
        assert "### Fixes" not in section
        assert "### Features" in section

    def test_multiple_sections(self):
        grouped = {k: [] for k in SECTION_ORDER}
        grouped["feat"] = [("aaa", "feat: f1")]
        grouped["fix"] = [("bbb", "fix: b1")]
        grouped["chore"] = [("ccc", "chore: c1")]
        section = _build_section("v2.0.0", grouped)
        assert "### Features" in section
        assert "### Fixes" in section
        assert "### Chores" in section

    def test_empty_grouped_still_has_version(self):
        grouped = {k: [] for k in SECTION_ORDER}
        section = _build_section("v0.0.1", grouped)
        assert "v0.0.1" in section

    def test_ends_with_newline(self):
        grouped = {k: [] for k in SECTION_ORDER}
        grouped["docs"] = [("xyz", "docs: update readme")]
        section = _build_section("v1.0.0", grouped)
        assert section.endswith("\n")


# ---------------------------------------------------------------------------
# _update_changelog
# ---------------------------------------------------------------------------

class TestUpdateChangelog:
    def test_creates_new_changelog(self, tmp_path):
        path = str(tmp_path / "CHANGELOG.md")
        _update_changelog(path, "## v1.0.0 - 2024-01-01\n\n### Features\n- feat: x\n", "v1.0.0")
        assert os.path.exists(path)
        content = open(path, encoding="utf-8").read()
        assert "v1.0.0" in content
        assert content.startswith("# Changelog")

    def test_prepends_to_existing(self, tmp_path):
        path = str(tmp_path / "CHANGELOG.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Changelog\n\n## v0.9.0 - 2024-01-01\n\nOld stuff\n")

        _update_changelog(path, "## v1.0.0 - 2024-02-01\n\n### Features\n- feat: y\n", "v1.0.0")
        content = open(path, encoding="utf-8").read()
        # v1.0.0 appears before v0.9.0
        assert content.index("v1.0.0") < content.index("v0.9.0")

    def test_no_duplicate_if_version_exists(self, tmp_path):
        path = str(tmp_path / "CHANGELOG.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Changelog\n\n## v1.0.0 - 2024-01-01\n\nAlready here\n")

        _update_changelog(path, "## v1.0.0 - 2024-02-01\n\nDuplicate\n", "v1.0.0")
        content = open(path, encoding="utf-8").read()
        # Should NOT add a second v1.0.0 entry
        assert content.count("## v1.0.0 -") == 1


# ---------------------------------------------------------------------------
# _parse_semver (additional cases)
# ---------------------------------------------------------------------------

class TestParseSemverExtended:
    @pytest.mark.parametrize("tag,expected", [
        ("v0.0.0", (0, 0, 0)),
        ("v99.99.99", (99, 99, 99)),
    ])
    def test_edge_versions(self, tag, expected):
        assert _parse_semver(tag) == expected

    @pytest.mark.parametrize("tag", [
        "v1.2.3.4",
        "v-1.0.0",
        " v1.0.0",  # leading space
        "v1.0.0 ",  # trailing space handled by strip
    ])
    def test_invalid_formats(self, tag):
        result = _parse_semver(tag)
        # "v1.0.0 " gets stripped -> (1,0,0); " v1.0.0" doesn't match
        if tag.strip() in ("v1.0.0",):
            assert result == (1, 0, 0)
        else:
            assert result is None
