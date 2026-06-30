"""Tests for benchmark_suite: _summary_table, _plot_report, and run_benchmark (mocked)."""
import json
import os
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from heat_simulation.benchmarks.benchmark_suite import (
    RunResult,
    _summary_table,
    _plot_report,
    _safe_seed,
    run_benchmark,
    _run_ga_once,
    _run_pso_once,
    _run_sa_once,
)


class TestSummaryTable:
    def test_single_algorithm_single_run(self):
        results = [RunResult("GA", 1, 0.5, 2.0)]
        df = _summary_table(results)
        assert len(df) == 1
        assert df.iloc[0]["algorithm"] == "GA"
        assert df.iloc[0]["runs"] == 1
        assert df.iloc[0]["best_objective_min"] == pytest.approx(0.5)
        assert df.iloc[0]["best_objective_std"] == pytest.approx(0.0)

    def test_multiple_algorithms(self):
        results = [
            RunResult("GA", 1, 0.5, 2.0),
            RunResult("GA", 2, 0.4, 2.5),
            RunResult("PSO", 1, 0.6, 1.5),
            RunResult("PSO", 2, 0.3, 1.8),
            RunResult("SA", 1, 0.7, 3.0),
        ]
        df = _summary_table(results)
        assert len(df) == 3
        # Sorted by best_objective_min ascending
        assert df.iloc[0]["best_objective_min"] <= df.iloc[1]["best_objective_min"]

    def test_statistics_computed_correctly(self):
        results = [
            RunResult("GA", 1, 1.0, 2.0),
            RunResult("GA", 2, 3.0, 4.0),
        ]
        df = _summary_table(results)
        row = df[df["algorithm"] == "GA"].iloc[0]
        assert row["runs"] == 2
        assert row["best_objective_min"] == pytest.approx(1.0)
        assert row["best_objective_mean"] == pytest.approx(2.0)
        assert row["time_mean_s"] == pytest.approx(3.0)
        assert row["time_max_s"] == pytest.approx(4.0)
        # pstdev of [1.0, 3.0] = 1.0
        assert row["best_objective_std"] == pytest.approx(1.0)

    def test_returns_dataframe(self):
        results = [RunResult("SA", 1, 0.2, 1.0)]
        df = _summary_table(results)
        assert isinstance(df, pd.DataFrame)
        expected_cols = {"algorithm", "runs", "best_objective_min", "best_objective_mean",
                        "best_objective_std", "time_mean_s", "time_max_s"}
        assert expected_cols.issubset(set(df.columns))


class TestPlotReport:
    def test_creates_png_file(self, tmp_path):
        df = pd.DataFrame([
            {"algorithm": "GA", "best_objective_min": 0.5, "time_mean_s": 2.0},
            {"algorithm": "PSO", "best_objective_min": 0.3, "time_mean_s": 1.5},
        ])
        out_png = str(tmp_path / "chart.png")
        _plot_report(df, out_png)
        assert os.path.exists(out_png)
        assert os.path.getsize(out_png) > 0

    def test_handles_single_algorithm(self, tmp_path):
        df = pd.DataFrame([
            {"algorithm": "SA", "best_objective_min": 0.8, "time_mean_s": 3.0},
        ])
        out_png = str(tmp_path / "single.png")
        _plot_report(df, out_png)
        assert os.path.exists(out_png)


class TestRunBenchmarkMocked:
    """Test run_benchmark with all optimizer calls mocked."""

    def _mock_ga(self, *args, **kwargs):
        return RunResult("GA", 0, 0.45, 1.0)

    def _mock_pso(self, *args, **kwargs):
        return RunResult("PSO", 0, 0.50, 0.8)

    def _mock_sa(self, *args, **kwargs):
        return RunResult("SA", 0, 0.55, 1.2)

    @patch("heat_simulation.benchmarks.benchmark_suite._run_sa_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_pso_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_ga_once")
    def test_run_benchmark_basic(self, mock_ga, mock_pso, mock_sa, tmp_path):
        mock_ga.side_effect = self._mock_ga
        mock_pso.side_effect = self._mock_pso
        mock_sa.side_effect = self._mock_sa

        profile_path = str(tmp_path / "profiles.json")
        with open(profile_path, "w") as f:
            json.dump({}, f)

        with patch("heat_simulation.benchmarks.benchmark_suite.REPORTS_DIR", tmp_path):
            result = run_benchmark(
                runs_per_algo=2,
                max_iteration_ga=10,
                profile="quick",
                profile_config_path=profile_path,
            )

        assert "details_csv" in result
        assert "summary_csv" in result
        assert "plot_png" in result
        assert "meta_json" in result
        assert os.path.exists(result["details_csv"])
        assert os.path.exists(result["summary_csv"])
        assert os.path.exists(result["plot_png"])
        assert os.path.exists(result["meta_json"])

    @patch("heat_simulation.benchmarks.benchmark_suite._run_sa_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_pso_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_ga_once")
    def test_meta_json_content(self, mock_ga, mock_pso, mock_sa, tmp_path):
        mock_ga.side_effect = self._mock_ga
        mock_pso.side_effect = self._mock_pso
        mock_sa.side_effect = self._mock_sa

        profile_path = str(tmp_path / "profiles.json")
        with open(profile_path, "w") as f:
            json.dump({}, f)

        with patch("heat_simulation.benchmarks.benchmark_suite.REPORTS_DIR", tmp_path):
            result = run_benchmark(
                runs_per_algo=1,
                max_iteration_ga=5,
                profile="quick",
                profile_config_path=profile_path,
            )

        with open(result["meta_json"]) as f:
            meta = json.load(f)

        assert meta["runs_per_algo"] == 1
        assert meta["profile"] == "quick"
        assert meta["best_algorithm"] == "GA"  # lowest objective
        assert "generated_at" in meta

    @patch("heat_simulation.benchmarks.benchmark_suite._run_sa_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_pso_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_ga_once")
    def test_unknown_profile_raises(self, mock_ga, mock_pso, mock_sa, tmp_path):
        profile_path = str(tmp_path / "profiles.json")
        with open(profile_path, "w") as f:
            json.dump({}, f)

        with patch("heat_simulation.benchmarks.benchmark_suite.REPORTS_DIR", tmp_path):
            with pytest.raises(ValueError, match="Unknown profile"):
                run_benchmark(
                    runs_per_algo=1,
                    max_iteration_ga=5,
                    profile="nonexistent",
                    profile_config_path=profile_path,
                )

    @patch("heat_simulation.benchmarks.benchmark_suite._run_sa_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_pso_once")
    @patch("heat_simulation.benchmarks.benchmark_suite._run_ga_once")
    def test_details_csv_has_all_runs(self, mock_ga, mock_pso, mock_sa, tmp_path):
        mock_ga.side_effect = self._mock_ga
        mock_pso.side_effect = self._mock_pso
        mock_sa.side_effect = self._mock_sa

        profile_path = str(tmp_path / "profiles.json")
        with open(profile_path, "w") as f:
            json.dump({}, f)

        with patch("heat_simulation.benchmarks.benchmark_suite.REPORTS_DIR", tmp_path):
            result = run_benchmark(
                runs_per_algo=3,
                max_iteration_ga=10,
                profile="quick",
                profile_config_path=profile_path,
            )

        details = pd.read_csv(result["details_csv"])
        assert len(details) == 9  # 3 algos * 3 runs
        assert set(details["algorithm"].unique()) == {"GA", "PSO", "SA"}


class TestRunGaOnce:
    """Test _run_ga_once with mocked GA_optimizer."""

    @patch("heat_simulation.benchmarks.benchmark_suite.GA_optimizer")
    def test_returns_run_result(self, mock_optimizer_cls):
        mock_instance = MagicMock()
        mock_instance.optimize.return_value = (None, [1.0, 0.8, 0.5])
        mock_optimizer_cls.return_value = mock_instance

        profile_cfg = {
            "ga_population": 10,
            "ga_nochange_iter": 5,
        }
        result = _run_ga_once(max_iteration=10, seed=42, profile_cfg=profile_cfg)
        assert result.algorithm == "GA"
        assert result.best_objective == pytest.approx(0.5)
        assert result.elapsed_seconds >= 0

    @patch("heat_simulation.benchmarks.benchmark_suite.GA_optimizer")
    def test_respects_max_runtime(self, mock_optimizer_cls):
        mock_instance = MagicMock()
        mock_instance.optimize.return_value = (None, [2.0])
        mock_optimizer_cls.return_value = mock_instance

        profile_cfg = {"ga_population": 10, "ga_nochange_iter": 5}
        result = _run_ga_once(max_iteration=5, seed=1, profile_cfg=profile_cfg, max_runtime_s=1.0)
        mock_instance.optimize.assert_called_once_with(max_iteration=5, verbose=False, max_wall_time_s=1.0)
        assert result.algorithm == "GA"


class TestRunPsoOnce:
    """Test _run_pso_once with mocked PSO."""

    @patch("heat_simulation.benchmarks.benchmark_suite.PSO")
    def test_returns_run_result(self, mock_pso_cls):
        mock_instance = MagicMock()
        mock_instance.run.return_value = 1.5
        mock_instance.gbest_hist = [1.0, 0.7, 0.4]
        mock_pso_cls.return_value = mock_instance

        profile_cfg = {"pso_population": 20, "pso_iterations": 10}
        result = _run_pso_once(seed=42, profile_cfg=profile_cfg)
        assert result.algorithm == "PSO"
        assert result.best_objective == pytest.approx(0.4)
        assert result.elapsed_seconds == pytest.approx(1.5)

    @patch("heat_simulation.benchmarks.benchmark_suite.PSO")
    def test_elapsed_zero_fallback(self, mock_pso_cls):
        mock_instance = MagicMock()
        mock_instance.run.return_value = 0  # elapsed = 0 triggers fallback
        mock_instance.gbest_hist = [1.0]
        mock_pso_cls.return_value = mock_instance

        profile_cfg = {"pso_population": 10, "pso_iterations": 5}
        result = _run_pso_once(seed=42, profile_cfg=profile_cfg)
        assert result.elapsed_seconds >= 0  # fallback to time.time()

    @patch("heat_simulation.benchmarks.benchmark_suite.PSO")
    def test_empty_gbest_hist(self, mock_pso_cls):
        mock_instance = MagicMock()
        mock_instance.run.return_value = 1.0
        mock_instance.gbest_hist = []
        mock_pso_cls.return_value = mock_instance

        profile_cfg = {"pso_population": 10, "pso_iterations": 5}
        result = _run_pso_once(seed=42, profile_cfg=profile_cfg)
        assert result.best_objective == float("inf")


class TestRunSaOnce:
    """Test _run_sa_once with mocked SA module."""

    @patch("heat_simulation.benchmarks.benchmark_suite.sa_module")
    def test_returns_run_result(self, mock_sa):
        mock_sa.main.return_value = (0.3, None, 2.5)

        profile_cfg = {
            "sa_num_iter": 100,
            "sa_t_max": 10,
            "sa_cooling_rate": 0.6,
            "sa_max_outer_iter": 50,
        }
        result = _run_sa_once(seed=42, profile_cfg=profile_cfg)
        assert result.algorithm == "SA"
        assert result.best_objective == pytest.approx(0.3)
        assert result.elapsed_seconds == pytest.approx(2.5)

    @patch("heat_simulation.benchmarks.benchmark_suite.sa_module")
    def test_elapsed_zero_fallback(self, mock_sa):
        mock_sa.main.return_value = (0.5, None, 0)  # elapsed = 0 triggers fallback

        profile_cfg = {
            "sa_num_iter": 100,
            "sa_t_max": 10,
            "sa_cooling_rate": 0.6,
            "sa_max_outer_iter": 50,
        }
        result = _run_sa_once(seed=42, profile_cfg=profile_cfg)
        assert result.elapsed_seconds >= 0
