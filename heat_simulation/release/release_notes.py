import argparse
import json
import os
import re
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


def _parse_semver(tag: str):
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _next_version(cwd: str, bump: str) -> str:
    latest = _latest_tag(cwd)
    parsed = _parse_semver(latest) if latest else (0, 0, 0)
    if parsed is None:
        raise RuntimeError(f"Latest tag is not semver-compatible: {latest}")

    major, minor, patch = parsed
    if bump == "patch":
        patch += 1
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        raise RuntimeError(f"Unsupported bump mode: {bump}")

    return f"v{major}.{minor}.{patch}"


def _collect_commits(
    cwd: str,
    commit_range: str,
    since_days: int | None = None,
    author: str | None = None,
    grep_text: str | None = None,
) -> List[Tuple[str, str]]:
    cmd = ["git", "log", "--pretty=format:%h%x09%s"]
    if since_days is not None:
        cmd.append(f"--since={since_days}.days")
    if author:
        cmd.append(f"--author={author}")
    if grep_text:
        cmd.append(f"--grep={grep_text}")
    cmd.append(commit_range)
    output = _run(cmd, cwd)
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


def prepare_release(
    base_dir: str,
    version: str,
    create_tag: bool,
    dry_run: bool,
    bump: str | None = None,
    from_tag: str | None = None,
    since_days: int | None = None,
    author: str | None = None,
    grep_text: str | None = None,
    require_nonempty: bool = False,
    output_json: str | None = None,
):
    if version and bump:
        raise RuntimeError("--version and --bump cannot be used together")
    if from_tag and since_days is not None:
        raise RuntimeError("--from-tag and --since-days cannot be used together")
    if since_days is not None and since_days <= 0:
        raise RuntimeError("--since-days must be a positive integer")

    if not version:
        if not bump:
            raise RuntimeError("Either --version or --bump must be provided")
        version = _next_version(base_dir, bump)

    if from_tag:
        if not _tag_exists(base_dir, from_tag):
            raise RuntimeError(f"from-tag does not exist: {from_tag}")
        commit_range = f"{from_tag}..HEAD"
    elif since_days is not None:
        commit_range = "HEAD"
    else:
        latest_tag = _latest_tag(base_dir)
        commit_range = f"{latest_tag}..HEAD" if latest_tag else "HEAD"

    commits = _collect_commits(
        base_dir,
        commit_range,
        since_days=since_days,
        author=author,
        grep_text=grep_text,
    )
    if require_nonempty and not commits:
        raise RuntimeError("No commits matched the selected release filters")

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

    output_payload = {
        "generated_at": datetime.now().isoformat(),
        "version": version,
        "commit_range": commit_range,
        "filters": {
            "from_tag": from_tag,
            "since_days": since_days,
            "author": author,
            "grep": grep_text,
            "require_nonempty": require_nonempty,
        },
        "commits": [{"hash": short_hash, "subject": subject} for short_hash, subject in commits],
        "changelog_path": changelog_path,
        "tag_created": tag_created,
        "dry_run": dry_run,
    }
    if output_json:
        output_dir = os.path.dirname(output_json)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, ensure_ascii=False, indent=2)

    range_text = f"last {since_days} day(s)" if since_days is not None else commit_range
    print(f"Prepared release notes for {version} from range: {range_text}")
    if author:
        print(f"Author filter: {author}")
    if grep_text:
        print(f"Keyword filter: {grep_text}")
    print(f"Commits included: {len(commits)}")
    print(f"Changelog path: {changelog_path}")
    if output_json:
        print(f"Output JSON: {output_json}")
    print(f"Tag created: {'yes' if tag_created else 'no'}")
    if dry_run:
        print("Dry run mode: no files/tags were changed")


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare changelog and optional local git tag for release.")
    parser.add_argument("--base-dir", default=".", help="Project root path")
    parser.add_argument("--version", required=False, help="Release version/tag, e.g. v0.2.0")
    parser.add_argument("--bump", choices=["patch", "minor"], help="Auto-calculate next semantic version from latest tag")
    parser.add_argument("--from-tag", help="Use an explicit tag as changelog range start, e.g. v0.1.0")
    parser.add_argument("--since-days", type=int, help="Use commits from the last N days as changelog source")
    parser.add_argument("--author", help="Only include commits whose author matches this pattern")
    parser.add_argument("--grep", dest="grep_text", help="Only include commits whose subject matches this keyword/regex")
    parser.add_argument("--require-nonempty", action="store_true", help="Fail if filters produce zero commits")
    parser.add_argument("--output-json", help="Optional path to export selected commits and release filters as JSON")
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
        bump=args.bump,
        from_tag=args.from_tag,
        since_days=args.since_days,
        author=args.author,
        grep_text=args.grep_text,
        require_nonempty=args.require_nonempty,
        output_json=args.output_json,
    )
