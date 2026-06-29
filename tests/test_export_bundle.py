"""Tests for heat_simulation.analysis.export_bundle."""
import io
import json
import os
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from heat_simulation.core.simulation_core import DEFAULT_IRRADIANCE, SimulationConfig, run_heat_simulation
from heat_simulation.analysis.comparison_dashboard import compare_scenarios
from heat_simulation.analysis.export_bundle import (
    collect_simulation_artifacts,
    collect_comparison_artifacts,
    build_manifest,
    pack_zip,
    create_report_bundle,
    zip_to_bytes,
)


# ---------------------------------------------------------------------------
# Shared fixtures (module-scoped for speed)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def small_cfg():
    return SimulationConfig(
        time_points=4,
        irradiance_values=DEFAULT_IRRADIANCE[:4],
    )


@pytest.fixture(scope="module")
def sim_result(small_cfg):
    return run_heat_simulation(small_cfg)


@pytest.fixture(scope="module")
def two_scenario_results():
    configs = {
        "Low Wind": SimulationConfig(
            time_points=4,
            irradiance_values=DEFAULT_IRRADIANCE[:4],
            wind_speed=1.0,
        ),
        "High Wind": SimulationConfig(
            time_points=4,
            irradiance_values=DEFAULT_IRRADIANCE[:4],
            wind_speed=6.0,
        ),
    }
    return compare_scenarios(configs)


# ---------------------------------------------------------------------------
# collect_simulation_artifacts
# ---------------------------------------------------------------------------

class TestCollectSimulationArtifacts:
    def test_creates_expected_files(self, sim_result, tmp_path):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim")
        assert "curves_csv" in paths
        assert "final_json" in paths
        assert "kpis_json" in paths

    def test_files_exist(self, sim_result, tmp_path):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim")
        for label, path in paths.items():
            assert os.path.exists(path), f"Missing: {label} -> {path}"

    def test_curves_csv_is_valid(self, sim_result, tmp_path):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim2")
        df = pd.read_csv(paths["curves_csv"], index_col=0)
        assert "T_water" in df.columns

    def test_kpis_json_is_valid(self, sim_result, tmp_path):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim3")
        with open(paths["kpis_json"]) as f:
            kpis = json.load(f)
        assert "peak_pv_temp_c" in kpis

    def test_final_json_is_valid(self, sim_result, tmp_path):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim4")
        with open(paths["final_json"]) as f:
            final = json.load(f)
        assert "T_water" in final

    def test_prefix_applied_to_filenames(self, sim_result, tmp_path):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim5", prefix="myrun")
        for path in paths.values():
            assert os.path.basename(path).startswith("myrun_")

    def test_creates_output_dir(self, sim_result, tmp_path):
        subdir = tmp_path / "nested" / "sim"
        collect_simulation_artifacts(sim_result, subdir)
        assert subdir.exists()


# ---------------------------------------------------------------------------
# collect_comparison_artifacts
# ---------------------------------------------------------------------------

class TestCollectComparisonArtifacts:
    def test_creates_csv_and_pngs(self, two_scenario_results, tmp_path):
        paths = collect_comparison_artifacts(two_scenario_results, tmp_path / "cmp")
        assert "kpi_comparison_csv" in paths
        assert "temperature_overlay_png" in paths
        assert "kpi_heatmap_png" in paths

    def test_all_files_exist(self, two_scenario_results, tmp_path):
        paths = collect_comparison_artifacts(two_scenario_results, tmp_path / "cmp2")
        for label, path in paths.items():
            assert os.path.exists(path), f"Missing: {label}"

    def test_kpi_csv_has_scenario_rows(self, two_scenario_results, tmp_path):
        paths = collect_comparison_artifacts(two_scenario_results, tmp_path / "cmp3")
        df = pd.read_csv(paths["kpi_comparison_csv"], index_col=0)
        assert len(df) == 2

    def test_png_is_nonzero(self, two_scenario_results, tmp_path):
        paths = collect_comparison_artifacts(two_scenario_results, tmp_path / "cmp4")
        size = os.path.getsize(paths["temperature_overlay_png"])
        assert size > 100  # definitely not empty


# ---------------------------------------------------------------------------
# build_manifest
# ---------------------------------------------------------------------------

class TestBuildManifest:
    def test_returns_dict(self):
        m = build_manifest({"a.csv": "/tmp/a.csv"})
        assert isinstance(m, dict)

    def test_has_generated_at(self):
        m = build_manifest({})
        assert "generated_at" in m

    def test_artifact_count(self):
        m = build_manifest({"x": "p1", "y": "p2"})
        assert m["artifact_count"] == 2

    def test_metadata_included(self):
        m = build_manifest({}, metadata={"version": "1.0"})
        assert m["metadata"]["version"] == "1.0"

    def test_no_metadata_key_when_none(self):
        m = build_manifest({})
        assert "metadata" not in m


# ---------------------------------------------------------------------------
# pack_zip
# ---------------------------------------------------------------------------

class TestPackZip:
    def test_creates_zip(self, tmp_path, sim_result):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim")
        zip_path = str(tmp_path / "out.zip")
        result = pack_zip(paths, zip_path)
        assert os.path.exists(result)

    def test_zip_contains_files(self, tmp_path, sim_result):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim2")
        zip_path = str(tmp_path / "out2.zip")
        pack_zip(paths, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        assert len(names) > 0

    def test_manifest_in_zip(self, tmp_path, sim_result):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim3")
        zip_path = str(tmp_path / "out3.zip")
        manifest = build_manifest(paths)
        pack_zip(paths, zip_path, manifest=manifest)
        with zipfile.ZipFile(zip_path, "r") as zf:
            assert "manifest.json" in zf.namelist()

    def test_extra_files(self, tmp_path):
        zip_path = str(tmp_path / "extra.zip")
        pack_zip({}, zip_path, extra_files=[("note.txt", "hello world")])
        with zipfile.ZipFile(zip_path, "r") as zf:
            content = zf.read("note.txt").decode()
        assert content == "hello world"

    def test_missing_artifact_skipped(self, tmp_path):
        zip_path = str(tmp_path / "skip.zip")
        paths = {"ghost": str(tmp_path / "nonexistent.csv")}
        pack_zip(paths, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            assert "nonexistent.csv" not in zf.namelist()

    def test_returns_absolute_path(self, tmp_path, sim_result):
        paths = collect_simulation_artifacts(sim_result, tmp_path / "sim4")
        zip_path = str(tmp_path / "abs.zip")
        result = pack_zip(paths, zip_path)
        assert os.path.isabs(result)


# ---------------------------------------------------------------------------
# create_report_bundle
# ---------------------------------------------------------------------------

class TestCreateReportBundle:
    def test_with_sim_result_only(self, sim_result, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "bundle1",
            sim_result=sim_result,
        )
        assert "zip_path" in bundle
        assert os.path.exists(bundle["zip_path"])

    def test_with_scenario_results(self, two_scenario_results, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "bundle2",
            scenario_results=two_scenario_results,
        )
        assert os.path.exists(bundle["zip_path"])

    def test_with_both(self, sim_result, two_scenario_results, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "bundle3",
            sim_result=sim_result,
            scenario_results=two_scenario_results,
        )
        assert "zip_path" in bundle
        # Should have artifacts from both
        assert len(bundle["artifacts"]) >= 3

    def test_no_inputs_raises(self, tmp_path):
        with pytest.raises(ValueError, match="At least one"):
            create_report_bundle(output_dir=tmp_path / "empty")

    def test_manifest_in_bundle(self, sim_result, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "bundle4",
            sim_result=sim_result,
        )
        assert "manifest" in bundle
        assert "generated_at" in bundle["manifest"]

    def test_extra_json_included(self, sim_result, tmp_path):
        extra = {"run_summary": {"version": "1.0", "note": "test run"}}
        bundle = create_report_bundle(
            output_dir=tmp_path / "bundle5",
            sim_result=sim_result,
            extra_json_files=extra,
        )
        assert "run_summary" in bundle["artifacts"]
        with zipfile.ZipFile(bundle["zip_path"], "r") as zf:
            names = zf.namelist()
        assert "run_summary" in names

    def test_custom_zip_name(self, sim_result, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "bundle6",
            sim_result=sim_result,
            zip_name="custom_name.zip",
        )
        assert bundle["zip_path"].endswith("custom_name.zip")


# ---------------------------------------------------------------------------
# zip_to_bytes
# ---------------------------------------------------------------------------

class TestZipToBytes:
    def test_returns_bytes(self, sim_result, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "zb",
            sim_result=sim_result,
        )
        data = zip_to_bytes(bundle["zip_path"])
        assert isinstance(data, bytes)

    def test_bytes_are_valid_zip(self, sim_result, tmp_path):
        bundle = create_report_bundle(
            output_dir=tmp_path / "zb2",
            sim_result=sim_result,
        )
        data = zip_to_bytes(bundle["zip_path"])
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert len(zf.namelist()) > 0
