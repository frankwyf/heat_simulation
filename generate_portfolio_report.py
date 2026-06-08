import argparse
import glob
import json
import os
from datetime import datetime

import pandas as pd


def _latest_meta(pattern: str = "reports/benchmark_meta_*.json") -> str:
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError("No benchmark meta file found in reports/. Run benchmark_runner.py first.")
    return files[-1]


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    rows = [headers]
    rows.extend([[str(v) for v in row] for row in df.values.tolist()])

    widths = [max(len(rows[r][c]) for r in range(len(rows))) for c in range(len(headers))]

    def fmt(row):
        return "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(row))) + " |"

    sep = "| " + " | ".join("-" * widths[i] for i in range(len(widths))) + " |"
    lines = [fmt(rows[0]), sep]
    for row in rows[1:]:
        lines.append(fmt(row))
    return "\n".join(lines)


def build_report(meta_path: str, output_path: str):
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    summary_csv = meta["artifacts"]["summary_csv"]
    chart_png = meta["artifacts"]["plot_png"]
    details_csv = meta["artifacts"]["details_csv"]

    summary = pd.read_csv(summary_csv)
    table_md = _df_to_markdown_table(summary)

    lines = []
    lines.append("# Industrial Optimization Benchmark Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().isoformat()}")
    lines.append(f"- Benchmark profile: {meta.get('profile', 'unknown')}")
    lines.append(f"- Runs per algorithm: {meta.get('runs_per_algo')}")
    lines.append(f"- GA max iteration: {meta.get('max_iteration_ga')}")
    lines.append(f"- Best algorithm (this run): {meta.get('best_algorithm')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(table_md)
    lines.append("")
    lines.append("## Chart")
    lines.append("")
    lines.append(f"![Benchmark chart]({chart_png})")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append(f"- Meta: {meta_path}")
    lines.append(f"- Summary CSV: {summary_csv}")
    lines.append(f"- Details CSV: {details_csv}")
    lines.append(f"- Chart PNG: {chart_png}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a portfolio-friendly markdown report from latest benchmark artifacts.")
    parser.add_argument("--meta", default=None, help="Path to benchmark meta json. Defaults to latest file in reports/.")
    parser.add_argument("--out", default="reports/portfolio_report.md", help="Output markdown file path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    meta_path = args.meta if args.meta else _latest_meta()
    build_report(meta_path=meta_path, output_path=args.out)
    print(f"Portfolio report generated: {args.out}")
