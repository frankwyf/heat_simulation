import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

from heat_simulation.core.paths import REPORTS_DIR


def _run(cmd: list[str], cwd: str):
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def main(base_dir: str):
    py = sys.executable

    compile_targets = [
        "solve.py",
        "app.py",
        "heat_simulation/core/simulation_core.py",
        "heat_simulation/tools/benchmark_runner.py",
        "heat_simulation/tools/generate_portfolio_report.py",
    ]
    _run([py, "-m", "py_compile", *compile_targets], cwd=base_dir)
    _run(
        [
            py,
            "solve.py",
            "--no-plot",
            "--save-path",
            str(REPORTS_DIR / "validation_result.png"),
            "--initial-temp-c",
            "22",
            "--ambient-temp-c",
            "30",
            "--wind-speed",
            "2.5",
        ],
        cwd=base_dir,
    )
    benchmark_output = _run([py, "-m", "heat_simulation.tools.benchmark_runner", "--runs", "1", "--ga-iter", "80", "--seed", "42", "--profile", "quick"], cwd=base_dir)
    report_output = _run([py, "-m", "heat_simulation.tools.generate_portfolio_report"], cwd=base_dir)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    validation_path = REPORTS_DIR / "validation_summary.json"
    with open(validation_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "validated_at": datetime.now().isoformat(),
                "python": py,
                "benchmark_output": benchmark_output,
                "report_output": report_output,
                "checks": [
                    "py_compile",
                    "solve_cli",
                    "benchmark_quick",
                    "portfolio_report",
                ],
                "status": "passed",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Validation passed. Summary: {validation_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full local pipeline validation for stable showcase delivery.")
    parser.add_argument("--base-dir", default=".", help="Project root directory.")
    args = parser.parse_args()
    main(os.path.abspath(args.base_dir))
