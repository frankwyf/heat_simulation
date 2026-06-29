"""Tests for heat_simulation.analysis.industrial_report (save_industrial_bundle)."""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from heat_simulation.analysis.industrial_report import save_industrial_bundle


@pytest.fixture
def minimal_bundle():
    return {
        "config": {"initial_temp_k": 293.15},
        "baseline_kpis": {"peak_pv_temp_c": 55.0},
    }


@pytest.fixture
def bundle_with_sensitivity():
    return {
        "config": {},
        "baseline_kpis": {},
        "sensitivity": [
            {"parameter": "wind_speed", "delta_ratio": 0.0, "metric_value": 20.0},
        ],
    }


@pytest.fixture
def bundle_with_monte_carlo():
    return {
        "config": {},
        "baseline_kpis": {},
        "monte_carlo": {
            "summary": {"samples": 3.0},
            "records": [
                {"sample_id": 1, "final_water_temp_c": 35.0},
                {"sample_id": 2, "final_water_temp_c": 36.0},
            ],
        },
    }


class TestSaveIndustrialBundle:
    def test_creates_json_file(self, tmp_path, minimal_bundle):
        exports = save_industrial_bundle(minimal_bundle, tmp_path)
        assert "analysis_json" in exports
        assert os.path.exists(exports["analysis_json"])

    def test_json_is_valid(self, tmp_path, minimal_bundle):
        exports = save_industrial_bundle(minimal_bundle, tmp_path)
        with open(exports["analysis_json"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["config"] == minimal_bundle["config"]

    def test_sensitivity_csv_created(self, tmp_path, bundle_with_sensitivity):
        exports = save_industrial_bundle(bundle_with_sensitivity, tmp_path)
        assert "sensitivity_csv" in exports
        df = pd.read_csv(exports["sensitivity_csv"])
        assert "parameter" in df.columns

    def test_monte_carlo_csv_created(self, tmp_path, bundle_with_monte_carlo):
        exports = save_industrial_bundle(bundle_with_monte_carlo, tmp_path)
        assert "monte_carlo_csv" in exports
        df = pd.read_csv(exports["monte_carlo_csv"])
        assert len(df) == 2

    def test_no_sensitivity_csv_when_missing(self, tmp_path, minimal_bundle):
        exports = save_industrial_bundle(minimal_bundle, tmp_path)
        assert "sensitivity_csv" not in exports

    def test_creates_output_dir(self, tmp_path):
        subdir = tmp_path / "nested" / "dir"
        bundle = {"config": {}, "baseline_kpis": {}}
        exports = save_industrial_bundle(bundle, subdir)
        assert subdir.exists()
        assert "analysis_json" in exports

    def test_name_prefix_applied(self, tmp_path, minimal_bundle):
        exports = save_industrial_bundle(minimal_bundle, tmp_path, name_prefix="mytest")
        filename = os.path.basename(exports["analysis_json"])
        assert filename.startswith("mytest_")

    def test_empty_sensitivity_list_no_csv(self, tmp_path):
        bundle = {"config": {}, "baseline_kpis": {}, "sensitivity": []}
        exports = save_industrial_bundle(bundle, tmp_path)
        assert "sensitivity_csv" not in exports

    def test_empty_mc_records_no_csv(self, tmp_path):
        bundle = {"config": {}, "baseline_kpis": {}, "monte_carlo": {"records": []}}
        exports = save_industrial_bundle(bundle, tmp_path)
        assert "monte_carlo_csv" not in exports
