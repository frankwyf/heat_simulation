"""Tests for heat_simulation.benchmarks.benchmark_suite (pure utility functions)."""
import json
import os

import pytest

from heat_simulation.benchmarks.benchmark_suite import (
    RunResult,
    _safe_seed,
    _load_profiles,
    _validate_profile_cfg,
    DEFAULT_PROFILE_SETTINGS,
    REQUIRED_PROFILE_KEYS,
)


class TestRunResult:
    def test_create_run_result(self):
        r = RunResult(algorithm="GA", trial=1, best_objective=0.5, elapsed_seconds=1.2)
        assert r.algorithm == "GA"
        assert r.trial == 1
        assert r.best_objective == pytest.approx(0.5)
        assert r.elapsed_seconds == pytest.approx(1.2)


class TestSafeSeed:
    def test_safe_seed_does_not_raise(self):
        _safe_seed(42)
        _safe_seed(0)


class TestLoadProfiles:
    def test_returns_default_if_file_missing(self, tmp_path):
        missing_path = str(tmp_path / "nonexistent.json")
        result = _load_profiles(missing_path)
        assert "quick" in result
        assert "standard" in result

    def test_loads_and_merges_existing(self, tmp_path):
        custom = {"quick": {"ga_population": 999}}
        path = str(tmp_path / "profiles.json")
        with open(path, "w") as f:
            json.dump(custom, f)
        result = _load_profiles(path)
        assert result["quick"]["ga_population"] == 999
        # Other keys should be merged from defaults
        assert "ga_nochange_iter" in result["quick"]

    def test_preserves_standard_profile(self, tmp_path):
        path = str(tmp_path / "profiles.json")
        with open(path, "w") as f:
            json.dump({}, f)
        result = _load_profiles(path)
        assert "standard" in result


class TestValidateProfileCfg:
    def test_valid_profile_does_not_raise(self):
        cfg = {k: 1 for k in REQUIRED_PROFILE_KEYS}
        _validate_profile_cfg("quick", cfg)  # should not raise

    def test_missing_key_raises(self):
        cfg = {k: 1 for k in REQUIRED_PROFILE_KEYS if k != "ga_population"}
        with pytest.raises(ValueError, match="ga_population"):
            _validate_profile_cfg("quick", cfg)

    def test_all_required_keys_present(self):
        assert len(REQUIRED_PROFILE_KEYS) > 0
        for key in REQUIRED_PROFILE_KEYS:
            assert isinstance(key, str)


class TestDefaultProfileSettings:
    def test_has_quick_and_standard(self):
        assert "quick" in DEFAULT_PROFILE_SETTINGS
        assert "standard" in DEFAULT_PROFILE_SETTINGS

    def test_all_required_keys_in_profiles(self):
        for profile_name, cfg in DEFAULT_PROFILE_SETTINGS.items():
            for key in REQUIRED_PROFILE_KEYS:
                assert key in cfg, f"Profile '{profile_name}' missing key '{key}'"

    def test_numeric_values(self):
        for profile_name, cfg in DEFAULT_PROFILE_SETTINGS.items():
            for key, val in cfg.items():
                assert isinstance(val, (int, float)), f"Profile '{profile_name}', key '{key}' is not numeric"
