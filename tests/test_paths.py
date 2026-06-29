"""Tests for heat_simulation.core.paths."""
from pathlib import Path

from heat_simulation.core.paths import (
    PROJECT_ROOT,
    CONFIGS_DIR,
    REPORTS_DIR,
    PROFILE_HISTORY_DIR,
    LEGACY_DIR,
    DEFAULT_BENCHMARK_PROFILE_PATH,
    DEFAULT_BENCHMARK_PROFILE_RELATIVE,
    BENCHMARK_META_GLOB,
    PORTFOLIO_REPORT_PATH,
    PUBLISH_READINESS_PATH,
)


class TestPaths:
    def test_project_root_is_directory(self):
        assert PROJECT_ROOT.is_dir()

    def test_configs_dir_under_root(self):
        assert CONFIGS_DIR.parent == PROJECT_ROOT

    def test_reports_dir_under_root(self):
        assert REPORTS_DIR.parent == PROJECT_ROOT

    def test_profile_history_under_reports(self):
        assert PROFILE_HISTORY_DIR.parent == REPORTS_DIR

    def test_legacy_dir_under_root(self):
        assert LEGACY_DIR.parent == PROJECT_ROOT

    def test_benchmark_profile_path_in_configs(self):
        assert DEFAULT_BENCHMARK_PROFILE_PATH.parent == CONFIGS_DIR

    def test_benchmark_profile_relative_is_string(self):
        assert isinstance(DEFAULT_BENCHMARK_PROFILE_RELATIVE, str)
        assert DEFAULT_BENCHMARK_PROFILE_RELATIVE.endswith(".json")

    def test_benchmark_meta_glob_is_string(self):
        assert isinstance(BENCHMARK_META_GLOB, str)
        assert "benchmark_meta" in BENCHMARK_META_GLOB

    def test_portfolio_report_path_is_md(self):
        assert str(PORTFOLIO_REPORT_PATH).endswith(".md")

    def test_publish_readiness_path_is_md(self):
        assert str(PUBLISH_READINESS_PATH).endswith(".md")

    def test_paths_are_path_objects(self):
        for p in (PROJECT_ROOT, CONFIGS_DIR, REPORTS_DIR, PROFILE_HISTORY_DIR,
                  LEGACY_DIR, DEFAULT_BENCHMARK_PROFILE_PATH,
                  PORTFOLIO_REPORT_PATH, PUBLISH_READINESS_PATH):
            assert isinstance(p, Path)
