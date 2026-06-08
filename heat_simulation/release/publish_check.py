import argparse
import json
import os
import subprocess
from datetime import datetime

from heat_simulation.core.paths import PUBLISH_READINESS_PATH, REPORTS_DIR


def _run(cmd: list[str], cwd: str) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        return f"[failed] {' '.join(cmd)}\n{result.stderr.strip()}"
    return result.stdout.strip()


def generate_checklist(base_dir: str, out_path: str):
    git_branch = _run(["git", "branch", "--show-current"], base_dir)
    git_status = _run(["git", "status", "--short"], base_dir)
    git_log = _run(["git", "log", "--oneline", "-n", "5"], base_dir)

    validation_path = REPORTS_DIR / "validation_summary.json"
    validation_exists = os.path.exists(validation_path)
    validation_summary = {}
    if validation_exists:
        with open(validation_path, "r", encoding="utf-8") as f:
            validation_summary = json.load(f)

    lines = []
    lines.append("# Publish Readiness Check")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().isoformat()}")
    lines.append(f"- Branch: {git_branch or 'unknown'}")
    lines.append("")
    lines.append("## Git Health")
    lines.append("")
    lines.append(f"- Working tree clean: {'yes' if not git_status else 'no'}")
    if git_status:
        lines.append("- Pending changes:")
        for row in git_status.splitlines():
            lines.append(f"  - {row}")
    lines.append("")
    lines.append("## Recent Commits")
    lines.append("")
    for row in (git_log.splitlines() if git_log else []):
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append(f"- validation_summary.json found: {'yes' if validation_exists else 'no'}")
    if validation_exists:
        lines.append(f"- validation status: {validation_summary.get('status', 'unknown')}")
        lines.append(f"- validated at: {validation_summary.get('validated_at', 'unknown')}")
        lines.append(f"- checks: {', '.join(validation_summary.get('checks', []))}")
    lines.append("")
    lines.append("## Ready To Publish")
    lines.append("")
    ready = (not git_status) and validation_exists and (validation_summary.get("status") == "passed")
    lines.append(f"- ready: {'yes' if ready else 'no'}")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Checklist generated: {out_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a publish-readiness check from git and local validation artifacts.")
    parser.add_argument("--base-dir", default=".", help="Project root path.")
    parser.add_argument("--out", default=str(PUBLISH_READINESS_PATH), help="Output markdown path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_checklist(base_dir=os.path.abspath(args.base_dir), out_path=os.path.abspath(args.out))
