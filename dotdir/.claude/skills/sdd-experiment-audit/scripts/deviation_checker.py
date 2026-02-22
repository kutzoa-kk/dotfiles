#!/usr/bin/env python3
"""
Deviation Checker for SDD ML Projects.

Parses the Deviation Log table in 00_HYPOTHESES.md and cross-references
with git history of docs/specs/*.md to find undocumented changes.

Usage:
    python deviation_checker.py \\
        --project-dir /path/to/project
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class CheckResult:
    """Immutable check result."""

    def __init__(self, name: str, passed: bool, message: str):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


class DeviationEntry:
    """Immutable deviation log entry."""

    def __init__(
        self,
        date: str,
        file_changed: str,
        description: str,
        rationale: str,
        impact: str,
    ):
        self.date = date
        self.file_changed = file_changed
        self.description = description
        self.rationale = rationale
        self.impact = impact

    @property
    def parsed_date(self) -> Optional[datetime]:
        """Parse date string to datetime."""
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(self.date, fmt)
            except ValueError:
                continue
        return None


class GitChange:
    """Immutable git change record."""

    def __init__(self, date: str, filename: str, commit_msg: str):
        self.date = date
        self.filename = filename
        self.commit_msg = commit_msg

    @property
    def parsed_date(self) -> Optional[datetime]:
        """Parse ISO date string."""
        try:
            return datetime.fromisoformat(self.date)
        except ValueError:
            return None


def parse_deviation_log(hypotheses_path: Path) -> list[DeviationEntry]:
    """Parse the Deviation Log table from 00_HYPOTHESES.md."""
    if not hypotheses_path.exists():
        return []

    text = hypotheses_path.read_text()

    # Find deviation log section
    log_match = re.search(
        r'(?:##\s*Deviation\s*Log|##\s*Deviations)(.*?)(?=\n##|\Z)',
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not log_match:
        return []

    section = log_match.group(1)
    entries: list[DeviationEntry] = []

    # Parse markdown table rows
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|-") or line.startswith("| -"):
            continue
        if "Date" in line and "File" in line:
            continue  # Header row

        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # Remove empty cells from leading/trailing |

        if len(cells) >= 3:
            entries.append(DeviationEntry(
                date=cells[0],
                file_changed=cells[1] if len(cells) > 1 else "",
                description=cells[2] if len(cells) > 2 else "",
                rationale=cells[3] if len(cells) > 3 else "",
                impact=cells[4] if len(cells) > 4 else "",
            ))

    return entries


def get_spec_git_changes(project_dir: Path) -> list[GitChange]:
    """Get git log for docs/specs/*.md files."""
    try:
        result = subprocess.run(
            [
                "git", "log",
                "--format=COMMIT:%aI %s",
                "--name-only",
                "--diff-filter=M",
                "--", "docs/specs/",
            ],
            capture_output=True, text=True,
            cwd=str(project_dir),
        )
    except FileNotFoundError:
        return []

    changes: list[GitChange] = []
    current_date = ""
    current_msg = ""

    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("COMMIT:"):
            parts = line[7:].split(" ", 1)
            current_date = parts[0] if parts else ""
            current_msg = parts[1] if len(parts) > 1 else ""
        elif line.endswith(".md") and current_date:
            changes.append(GitChange(
                date=current_date,
                filename=line,
                commit_msg=current_msg,
            ))

    return changes


def check_deviation_coverage(
    project_dir: Path,
) -> CheckResult:
    """Check that all spec changes are documented in the Deviation Log."""
    hyp_path = project_dir / "docs" / "specs" / "00_HYPOTHESES.md"

    if not hyp_path.exists():
        return CheckResult(
            "Deviation Coverage",
            False,
            "00_HYPOTHESES.md not found. Cannot check deviation coverage.",
        )

    deviations = parse_deviation_log(hyp_path)
    git_changes = get_spec_git_changes(project_dir)

    if not git_changes:
        return CheckResult(
            "Deviation Coverage",
            True,
            "No spec modifications found in git history.",
        )

    # Build set of documented file changes
    documented_files = {d.file_changed.strip() for d in deviations}
    # Normalize to just filenames
    documented_basenames = set()
    for f in documented_files:
        documented_basenames.add(f)
        documented_basenames.add(Path(f).name)
        documented_basenames.add(str(Path("docs/specs") / Path(f).name))

    undocumented: list[GitChange] = []
    for change in git_changes:
        basename = Path(change.filename).name
        full_path = change.filename
        if (
            basename not in documented_basenames
            and full_path not in documented_basenames
        ):
            undocumented.append(change)

    if undocumented:
        details = "; ".join(
            f"{c.filename} ({c.date[:10]})"
            for c in undocumented[:5]
        )
        return CheckResult(
            "Deviation Coverage",
            False,
            f"{len(undocumented)} spec change(s) not in Deviation Log: {details}",
        )

    return CheckResult(
        "Deviation Coverage",
        True,
        f"All {len(git_changes)} spec change(s) documented. "
        f"{len(deviations)} deviation entries found.",
    )


def check_deviation_completeness(
    project_dir: Path,
) -> CheckResult:
    """Check that deviation entries have required fields."""
    hyp_path = project_dir / "docs" / "specs" / "00_HYPOTHESES.md"

    if not hyp_path.exists():
        return CheckResult(
            "Deviation Completeness",
            True,
            "No 00_HYPOTHESES.md found. Skipping.",
        )

    deviations = parse_deviation_log(hyp_path)
    if not deviations:
        return CheckResult(
            "Deviation Completeness",
            True,
            "No deviation entries found.",
        )

    incomplete: list[str] = []
    for d in deviations:
        missing = []
        if not d.date.strip():
            missing.append("date")
        if not d.file_changed.strip():
            missing.append("file")
        if not d.description.strip():
            missing.append("description")
        if missing:
            incomplete.append(f"Entry '{d.date}': missing {', '.join(missing)}")

    if incomplete:
        return CheckResult(
            "Deviation Completeness",
            False,
            f"{len(incomplete)} incomplete entries: {'; '.join(incomplete[:3])}",
        )

    return CheckResult(
        "Deviation Completeness",
        True,
        f"All {len(deviations)} deviation entries are complete.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deviation Checker: Verify spec changes are documented"
    )
    parser.add_argument(
        "--project-dir", type=Path, required=True,
        help="Root directory of the SDD ML project",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()

    results: list[CheckResult] = [
        check_deviation_coverage(project_dir),
        check_deviation_completeness(project_dir),
    ]

    # Report
    print("\n=== Deviation Checker Report ===\n")
    all_passed = True
    for r in results:
        print(r)
        if not r.passed:
            all_passed = False

    print(f"\n{'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
