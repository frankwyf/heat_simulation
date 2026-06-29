"""Tests for pure functions in release and portfolio_text modules."""
import pytest

from heat_simulation.core.portfolio_text import get_text, TEXT_ZH, TEXT_EN, I18NText
from heat_simulation.release.release_notes import (
    _parse_semver,
    _group_commits,
    SECTION_ORDER,
    SECTION_TITLES,
)


# ---------------------------------------------------------------------------
# portfolio_text
# ---------------------------------------------------------------------------

class TestPortfolioText:
    def test_get_text_english(self):
        t = get_text("English")
        assert isinstance(t, I18NText)
        assert t is TEXT_EN

    def test_get_text_chinese(self):
        t = get_text("中文")
        assert isinstance(t, I18NText)
        assert t is TEXT_ZH

    def test_get_text_fallback(self):
        t = get_text("Unknown")
        assert t is TEXT_ZH  # fallback

    def test_en_text_non_empty(self):
        for field in (TEXT_EN.title, TEXT_EN.subtitle, TEXT_EN.run_button,
                      TEXT_EN.tab_system, TEXT_EN.tab_optimizer):
            assert len(field) > 0

    def test_zh_text_non_empty(self):
        for field in (TEXT_ZH.title, TEXT_ZH.subtitle, TEXT_ZH.run_button,
                      TEXT_ZH.tab_system, TEXT_ZH.tab_optimizer):
            assert len(field) > 0

    def test_en_and_zh_differ(self):
        assert TEXT_EN.title != TEXT_ZH.title


# ---------------------------------------------------------------------------
# release_notes._parse_semver
# ---------------------------------------------------------------------------

class TestParseSemver:
    @pytest.mark.parametrize("tag,expected", [
        ("v1.2.3", (1, 2, 3)),
        ("1.0.0", (1, 0, 0)),
        ("v0.9.15", (0, 9, 15)),
        ("v10.20.30", (10, 20, 30)),
    ])
    def test_valid_tags(self, tag, expected):
        assert _parse_semver(tag) == expected

    @pytest.mark.parametrize("tag", [
        "v1.2",
        "1.2",
        "latest",
        "",
        "v1.2.3-beta",
        "abc",
    ])
    def test_invalid_tags_return_none(self, tag):
        assert _parse_semver(tag) is None


# ---------------------------------------------------------------------------
# release_notes._group_commits
# ---------------------------------------------------------------------------

class TestGroupCommits:
    def test_empty_commits(self):
        grouped = _group_commits([])
        for section in SECTION_ORDER:
            assert grouped[section] == []

    def test_feat_commit(self):
        commits = [("abc1234", "feat: add new feature")]
        grouped = _group_commits(commits)
        assert len(grouped["feat"]) == 1
        assert grouped["feat"][0][0] == "abc1234"

    def test_fix_commit(self):
        commits = [("bcd5678", "fix: resolve null pointer")]
        grouped = _group_commits(commits)
        assert len(grouped["fix"]) == 1

    def test_unknown_prefix_goes_to_other(self):
        commits = [("cde9012", "initial commit")]
        grouped = _group_commits(commits)
        assert len(grouped["other"]) == 1

    def test_multiple_commits(self):
        commits = [
            ("aaa", "feat: feature A"),
            ("bbb", "fix: bug fix"),
            ("ccc", "feat: feature B"),
            ("ddd", "chore: update deps"),
        ]
        grouped = _group_commits(commits)
        assert len(grouped["feat"]) == 2
        assert len(grouped["fix"]) == 1
        assert len(grouped["chore"]) == 1

    def test_all_section_order_keys_present(self):
        grouped = _group_commits([])
        for key in SECTION_ORDER:
            assert key in grouped

    def test_no_colon_goes_to_other(self):
        commits = [("fff", "just a plain message")]
        grouped = _group_commits(commits)
        assert len(grouped["other"]) == 1

    def test_case_insensitive_prefix(self):
        # "Feat" with capital F is lowered to "feat" before lookup
        commits = [("ggg", "Feat: capital prefix")]
        grouped = _group_commits(commits)
        assert len(grouped["feat"]) == 1


class TestSectionConstants:
    def test_all_orders_have_titles(self):
        for key in SECTION_ORDER:
            assert key in SECTION_TITLES

    def test_titles_are_non_empty(self):
        for key, title in SECTION_TITLES.items():
            assert isinstance(title, str) and len(title) > 0

