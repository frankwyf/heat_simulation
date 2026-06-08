import argparse
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple


SECTION_ORDER = ["feat", "fix", "perf", "refactor", "docs", "test", "chore", "other"]
SECTION_TITLES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactors",
    "docs": "Docs",
    "test": "Tests",
    "chore": "Chores",
    "other": "Other",
}


def _run(cmd: List[str], cwd: str) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def _latest_tag(cwd: str) -> str:
    try:
        return _run(["git", "describe", "--tags", "--abbrev=0"], cwd)
    except Exception:
        return ""


def _collect_commits(cwd: str, commit_range: str) -> List[Tuple[str, str]]:
    output = _run(["git", "log", "--pretty=format:%h%x09%s", commit_range], cwd)
    rows: List[Tuple[str, str]] = []
    for line in output.splitlines():
        if "\t" not in line:
            continue
        short_hash, subject = line.split("\t", 1)
        rows.append((short_hash.strip(), subject.strip()))
    return rows


def _group_commits(commits: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, str]]]:
    grouped: Dict[str, List[Tuple[str, str]]] = {k: [] for k in SECTION_ORDER}
    for short_hash, subject in commits:
        prefix = "other"
        if ":" in subject:
            maybe = subject.split(":", 1)[0].strip().lower()
            if maybe in grouped:
                prefix = maybe
        grouped[prefix].append((short_hash, subject))
    return grouped


def _build_section(version: str, grouped: Dict[str, List[Tuple[str, str]]]) -> str:
    lines = []
    lines.append(f"## {version} - {datetime.now().date().isoformat()}")
    lines.append("")
    for key in SECTION_ORDER:
        items = grouped.get(key, [])
        if not items:
            continue
        lines.append(f"### {SECTION_TITLES[key]}")
        for short_hash, subject in items:
            lines.append(f"- {subject} ({short_hash})")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _update_changelog(changelog_path: str, section_text: str, version: str):
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = "# Changelog\n\n"

    if f"## {version} -" in existing:
        return

    header = "# Changelog\n\n"
    body = existing[len(header):] if existing.startswith(header) else existing
    updated = header + section_text + "\n" + body.lstrip("\n")

    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(updated)


def _tag_exists(cwd: str, tag: str) -> bool:
    try:
        _run(["git", "rev-parse", "--verify", tag], cwd)
        return True
    except Exception:
        return False


def prepare_release(base_dir: str, version: str, create_tag: bool, dry_run: bool):
    latest_tag = _latest_tag(base_dir)
    commit_range = f"{latest_tag}..HEAD" if latest_tag else "HEAD"
    commits = _collect_commits(base_dir, commit_range)
    grouped = _group_commits(commits)

    changelog_path = os.path.join(base_dir, "CHANGELOG.md")
    section = _build_section(version, grouped)

    if not dry_run:
        _update_changelog(changelog_path, section, version)

    tag_created = False
    if create_tag:
        if _tag_exists(base_dir, version):
            raise RuntimeError(f"Tag already exists: {version}")
        if not dry_run:
            _run(["git", "tag", "-a", version, "-m", f"Release {version}"], base_dir)
        tag_created = True

    print(f"Prepared release notes for {version} from range: {commit_range}")
    print(f"Commits included: {len(commits)}")
    print(f"Changelog path: {changelog_path}")
    print(f"Tag created: {'yes' if tag_created else 'no'}")
    if dry_run:
        print("Dry run mode: no files/tags were changed")


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare changelog and optional local git tag for release.")
    parser.add_argument("--base-dir", default=".", help="Project root path")
    parser.add_argument("--version", required=True, help="Release version/tag, e.g. v0.2.0")
    parser.add_argument("--create-tag", action="store_true", help="Create local annotated git tag")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing files/tags")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    prepare_release(
        base_dir=os.path.abspath(args.base_dir),
        version=args.version,
        create_tag=args.create_tag,
        dry_run=args.dry_run,
    )
