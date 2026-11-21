#!/usr/bin/env python3
"""Report skill sharing by filesystem identity without changing any files."""

import argparse
import json
import os
from pathlib import Path


def same_directory(source: Path, target: Path) -> bool:
    try:
        return target.is_dir() and source.samefile(target)
    except (OSError, RuntimeError):
        return False


def check_sharing(repo: Path, home: Path, codex_home: Path) -> dict:
    source_root = repo / "dotdir/.claude/skills"
    destinations = {
        "user": home / ".agents/skills",
        "repo": repo / ".agents/skills",
        "legacy": codex_home / "skills",
    }
    report = {
        "source": str(source_root),
        "destinations": {key: str(path) for key, path in destinations.items()},
        "shared": [],
        "legacy_only": [],
        "unshared": [],
        "conflicts": [],
        "broken_sources": [],
    }
    for source in sorted(source_root.iterdir()):
        if source.name.startswith("."):
            continue
        if source.is_symlink() and not source.is_dir():
            report["broken_sources"].append(source.name)
            continue
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        matches = []
        for scope, root in destinations.items():
            target = root / source.name
            if same_directory(source, target):
                matches.append(scope)
            elif target.exists() or target.is_symlink():
                report["conflicts"].append({
                    "name": source.name,
                    "scope": scope,
                    "path": str(target),
                    "reason": "broken_link" if target.is_symlink() and not target.exists()
                    else "different_entry",
                })
        if "user" in matches or "repo" in matches:
            report["shared"].append(source.name)
        elif "legacy" in matches:
            report["legacy_only"].append(source.name)
        else:
            report["unshared"].append(source.name)
    report["counts"] = {key: len(report[key]) for key in (
        "shared", "legacy_only", "unshared", "conflicts", "broken_sources",
    )}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--codex-home", type=Path, help="defaults to CODEX_HOME or HOME/.codex")
    args = parser.parse_args()
    codex_home = args.codex_home or Path(os.environ.get("CODEX_HOME") or args.home / ".codex")
    try:
        report = check_sharing(args.repo.expanduser().resolve(), args.home.expanduser().resolve(),
                               codex_home.expanduser().resolve())
    except OSError as error:
        parser.exit(1, f"共有状況を確認できません: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
