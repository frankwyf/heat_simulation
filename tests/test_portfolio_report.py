"""Tests for heat_simulation.benchmarks.portfolio_report."""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from heat_simulation.benchmarks.portfolio_report import (
    _df_to_markdown_table,
    _relative_artifact_path,
)


class TestDfToMarkdownTable:
    def test_contains_header_and_separator(self):
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        md = _df_to_markdown_table(df)
        lines = md.splitlines()
        assert len(lines) >= 3
        # second line is separator (uses single dashes: "| - | - |")
        assert "-" in lines[1] and "|" in lines[1]

    def test_column_names_in_output(self):
        df = pd.DataFrame({"Algorithm": ["GA"], "Score": [0.5]})
        md = _df_to_markdown_table(df)
        assert "Algorithm" in md
        assert "Score" in md

    def test_data_values_in_output(self):
        df = pd.DataFrame({"X": [42]})
        md = _df_to_markdown_table(df)
        assert "42" in md

    def test_row_count(self):
        df = pd.DataFrame({"X": range(5)})
        md = _df_to_markdown_table(df)
        # header + separator + 5 data rows = 7 lines
        assert len(md.splitlines()) == 7

    def test_single_column(self):
        df = pd.DataFrame({"Only": ["val"]})
        md = _df_to_markdown_table(df)
        assert "Only" in md
        assert "val" in md

    def test_pipe_delimited(self):
        df = pd.DataFrame({"A": [1]})
        md = _df_to_markdown_table(df)
        assert "|" in md


class TestRelativeArtifactPath:
    def test_same_dir(self, tmp_path):
        artifact = str(tmp_path / "artifact.csv")
        output = str(tmp_path / "report.md")
        rel = _relative_artifact_path(artifact, output)
        assert rel == "artifact.csv"

    def test_forward_slash(self, tmp_path):
        artifact = str(tmp_path / "sub" / "artifact.csv")
        output = str(tmp_path / "report.md")
        rel = _relative_artifact_path(artifact, output)
        assert "\\" not in rel

    def test_relative_to_parent(self, tmp_path):
        subdir = tmp_path / "reports"
        subdir.mkdir()
        artifact = str(tmp_path / "data.csv")
        output = str(subdir / "report.md")
        rel = _relative_artifact_path(artifact, output)
        assert rel.startswith("..") or rel == "data.csv"


class TestBuildReport:
    def test_build_report_creates_file(self, tmp_path):
        from heat_simulation.benchmarks.portfolio_report import build_report

        # Minimal valid summary CSV
        summary_df = pd.DataFrame({
            "Algorithm": ["GA", "PSO", "SA"],
            "Mean": [1.0, 1.1, 1.2],
            "Std": [0.1, 0.1, 0.1],
            "Best": [0.9, 1.0, 1.1],
        })
        summary_csv = str(tmp_path / "summary.csv")
        summary_df.to_csv(summary_csv, index=False)

        # Dummy chart PNG
        chart_png = str(tmp_path / "chart.png")
        Path(chart_png).write_bytes(b"\x89PNG")

        # Dummy details CSV
        details_csv = str(tmp_path / "details.csv")
        pd.DataFrame({"algo": ["GA"], "trial": [1], "best": [1.0], "time": [1.0]}).to_csv(details_csv, index=False)

        # Dummy meta JSON
        meta = {
            "profile": "quick",
            "runs_per_algo": 1,
            "max_iteration_ga": 80,
            "best_algorithm": "GA",
            "artifacts": {
                "summary_csv": summary_csv,
                "plot_png": chart_png,
                "details_csv": details_csv,
            },
        }
        meta_path = str(tmp_path / "meta.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        output_path = str(tmp_path / "report.md")
        build_report(meta_path, output_path)
        assert os.path.exists(output_path)

        content = Path(output_path).read_text(encoding="utf-8")
        assert "Industrial Optimization Benchmark Report" in content
        assert "GA" in content
