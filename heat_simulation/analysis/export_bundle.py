"""One-click export bundle: collects all artifacts into a ZIP data package.

Provides a clean, self-contained archive of simulation results, analysis
outputs, benchmark artifacts, and reports suitable for hand-off or archiving.
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from heat_simulation.core.simulation_core import SimulationConfig, run_heat_simulation
from heat_simulation.analysis.industrial_analysis import (
    compute_industrial_kpis,
    build_industrial_analysis_bundle,
)
from heat_simulation.analysis.industrial_report import save_industrial_bundle
from heat_simulation.analysis.comparison_dashboard import (
    build_kpi_comparison_df,
    build_temperature_comparison_chart,
    build_multi_kpi_heatmap,
    save_comparison_figure,
)


# ---------------------------------------------------------------------------
# Data-collection helpers
# ---------------------------------------------------------------------------

def collect_simulation_artifacts(
    sim_result: dict,
    output_dir: Path,
    prefix: str = "sim",
) -> Dict[str, str]:
    """Persist a single simulation result to CSV and return file paths.

    Args:
        sim_result: Output of run_heat_simulation().
        output_dir: Directory to write files to (created if missing).
        prefix: File name prefix.

    Returns:
        Dict mapping artifact label -> file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}

    # Temperature curves CSV
    curves = sim_result["curves"]
    df = pd.DataFrame(curves, index=sim_result["time_labels"])
    df.index.name = "time"
    curves_path = str(output_dir / f"{prefix}_curves.csv")
    df.to_csv(curves_path)
    paths["curves_csv"] = curves_path

    # Final results JSON
    final_path = str(output_dir / f"{prefix}_final.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(sim_result["final_result"], f, indent=2)
    paths["final_json"] = final_path

    # KPI JSON
    kpis = compute_industrial_kpis(sim_result)
    kpi_path = str(output_dir / f"{prefix}_kpis.json")
    with open(kpi_path, "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=2)
    paths["kpis_json"] = kpi_path

    return paths


def collect_comparison_artifacts(
    scenario_results: Dict[str, dict],
    output_dir: Path,
    prefix: str = "comparison",
) -> Dict[str, str]:
    """Persist multi-scenario comparison artifacts.

    Args:
        scenario_results: Output of compare_scenarios().
        output_dir: Directory to write files to.
        prefix: File name prefix.

    Returns:
        Dict mapping artifact label -> file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}

    # KPI comparison CSV
    kpi_df = build_kpi_comparison_df(scenario_results)
    kpi_csv = str(output_dir / f"{prefix}_kpi_table.csv")
    kpi_df.to_csv(kpi_csv)
    paths["kpi_comparison_csv"] = kpi_csv

    # Temperature overlay chart
    fig_temp = build_temperature_comparison_chart(scenario_results, curve_key="T_water")
    temp_png = str(output_dir / f"{prefix}_temp_overlay.png")
    save_comparison_figure(fig_temp, temp_png)
    paths["temperature_overlay_png"] = temp_png

    # KPI heatmap
    fig_heatmap = build_multi_kpi_heatmap(kpi_df)
    heatmap_png = str(output_dir / f"{prefix}_kpi_heatmap.png")
    save_comparison_figure(fig_heatmap, heatmap_png)
    paths["kpi_heatmap_png"] = heatmap_png

    return paths


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def build_manifest(
    artifacts: Dict[str, str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a manifest dict describing the export bundle.

    Args:
        artifacts: Mapping of label -> file path (absolute or relative).
        metadata: Optional extra metadata to include.

    Returns:
        Manifest dict.
    """
    manifest: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    if metadata:
        manifest["metadata"] = metadata
    return manifest


# ---------------------------------------------------------------------------
# ZIP packing
# ---------------------------------------------------------------------------

def pack_zip(
    artifact_paths: Dict[str, str],
    zip_path: str,
    manifest: Optional[Dict[str, Any]] = None,
    extra_files: Optional[List[Tuple[str, str]]] = None,
) -> str:
    """Pack all artifact files into a ZIP archive.

    Args:
        artifact_paths: Mapping of label -> absolute file path to include.
        zip_path: Destination ZIP file path.
        manifest: Optional manifest dict (written as manifest.json inside ZIP).
        extra_files: Optional list of (arcname, content_str) tuples to add.

    Returns:
        Absolute path to the created ZIP file.
    """
    Path(zip_path).parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for label, path in artifact_paths.items():
            if not os.path.exists(path):
                continue
            arcname = os.path.basename(path)
            zf.write(path, arcname=arcname)

        if manifest is not None:
            manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            zf.writestr("manifest.json", manifest_bytes)

        for arcname, content in (extra_files or []):
            zf.writestr(arcname, content.encode("utf-8") if isinstance(content, str) else content)

    return str(Path(zip_path).resolve())


# ---------------------------------------------------------------------------
# High-level one-click API
# ---------------------------------------------------------------------------

def create_report_bundle(
    output_dir: str | Path,
    sim_result: Optional[dict] = None,
    scenario_results: Optional[Dict[str, dict]] = None,
    analysis_bundle: Optional[Dict[str, Any]] = None,
    extra_json_files: Optional[Dict[str, Any]] = None,
    zip_name: Optional[str] = None,
) -> Dict[str, Any]:
    """One-click: collect all available artifacts and pack into a ZIP.

    At least one of sim_result, scenario_results, or analysis_bundle must
    be provided.

    Args:
        output_dir: Working directory for intermediate files.
        sim_result: Single simulation result dict (optional).
        scenario_results: Multi-scenario results dict (optional).
        analysis_bundle: Industrial analysis bundle dict (optional).
        extra_json_files: Dict of filename -> dict to serialise into bundle.
        zip_name: Override ZIP filename (default: bundle_<timestamp>.zip).

    Returns:
        Dict with keys:
          - ``zip_path``: Path to the created ZIP file.
          - ``artifacts``: All collected artifact paths.
          - ``manifest``: The manifest dict written into the ZIP.
    """
    if sim_result is None and scenario_results is None and analysis_bundle is None:
        raise ValueError("At least one of sim_result, scenario_results, or analysis_bundle must be provided")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_artifacts: Dict[str, str] = {}

    # Single simulation artifacts
    if sim_result is not None:
        sim_artifacts = collect_simulation_artifacts(sim_result, out / "simulation")
        all_artifacts.update(sim_artifacts)

    # Multi-scenario comparison artifacts
    if scenario_results is not None and len(scenario_results) >= 2:
        cmp_artifacts = collect_comparison_artifacts(scenario_results, out / "comparison")
        all_artifacts.update(cmp_artifacts)

    # Industrial analysis bundle
    if analysis_bundle is not None:
        bundle_exports = save_industrial_bundle(analysis_bundle, out / "analysis")
        all_artifacts.update(bundle_exports)

    # Extra JSON files
    for filename, payload in (extra_json_files or {}).items():
        extra_path = out / filename
        with open(extra_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        all_artifacts[filename] = str(extra_path)

    # Build manifest
    manifest = build_manifest(all_artifacts, metadata={
        "has_simulation": sim_result is not None,
        "has_comparison": scenario_results is not None,
        "has_analysis_bundle": analysis_bundle is not None,
    })

    # Pack ZIP
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = zip_name or f"bundle_{ts}.zip"
    zip_path = pack_zip(all_artifacts, str(out / zip_filename), manifest=manifest)

    return {
        "zip_path": zip_path,
        "artifacts": all_artifacts,
        "manifest": manifest,
    }


def zip_to_bytes(zip_path: str) -> bytes:
    """Read a ZIP file and return its raw bytes (for Streamlit download_button).

    Args:
        zip_path: Path to the ZIP file.

    Returns:
        Raw bytes of the ZIP.
    """
    with open(zip_path, "rb") as f:
        return f.read()
