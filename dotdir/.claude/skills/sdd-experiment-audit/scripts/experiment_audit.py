#!/usr/bin/env python3
"""
Experiment Audit for SDD ML Projects.

Runs 5 checks to enforce SDD prime rules:
1. Deleted Runs (R5): No experiment runs have been deleted
2. Hold-out Count (R7): At most 1 hold-out run exists
3. Gate Conditions (R7): CV gate met before hold-out
4. Pre-Registration Timing (R9): Hypotheses committed before first run
5. Spec Drift (R9): No undocumented post-experiment spec changes

Usage:
    python experiment_audit.py \\
        --project-dir /path/to/project \\
        --backend mlflow \\
        --tracking-uri http://localhost:5000 \\
        --experiment-name my-experiment
"""

import argparse
import json
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


class RunInfo:
    """Immutable experiment run record."""

    def __init__(
        self,
        run_id: str,
        status: str,
        start_time: str,
        end_time: Optional[str],
        tags: dict[str, str],
        metrics: dict[str, float],
        is_deleted: bool,
    ):
        self.run_id = run_id
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.tags = tags
        self.metrics = metrics
        self.is_deleted = is_deleted

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Parse start_time to datetime."""
        if not self.start_time:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(self.start_time[:19], fmt[:19])
            except ValueError:
                continue
        return None

    @property
    def is_holdout(self) -> bool:
        """Check if this run is tagged as hold-out."""
        phase = self.tags.get("phase", "").lower()
        holdout_tag = self.tags.get("holdout", "").lower()
        return phase == "holdout" or holdout_tag == "true"


# ---------------------------------------------------------------------------
# Backend Loaders
# ---------------------------------------------------------------------------

def load_runs_mlflow(
    tracking_uri: str,
    experiment_name: str,
) -> list[RunInfo]:
    """Load runs from MLflow backend."""
    try:
        from mlflow.tracking import MlflowClient
        from mlflow.entities import ViewType
    except ImportError:
        print("ERROR: mlflow not installed. Run: pip install mlflow", file=sys.stderr)
        sys.exit(1)

    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        print(f"ERROR: Experiment '{experiment_name}' not found", file=sys.stderr)
        sys.exit(1)

    all_runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        run_view_type=ViewType.ALL,
        max_results=10000,
    )

    results: list[RunInfo] = []
    for run in all_runs:
        start_ms = run.info.start_time
        end_ms = run.info.end_time
        results.append(RunInfo(
            run_id=run.info.run_id,
            status=run.info.status,
            start_time=datetime.fromtimestamp(start_ms / 1000).isoformat() if start_ms else "",
            end_time=datetime.fromtimestamp(end_ms / 1000).isoformat() if end_ms else None,
            tags=dict(run.data.tags),
            metrics=dict(run.data.metrics),
            is_deleted=(run.info.lifecycle_stage == "deleted"),
        ))
    return results


def load_runs_wandb(
    entity: str,
    wandb_project: str,
) -> list[RunInfo]:
    """Load runs from W&B backend."""
    try:
        import wandb
    except ImportError:
        print("ERROR: wandb not installed. Run: pip install wandb", file=sys.stderr)
        sys.exit(1)

    api = wandb.Api()
    runs = api.runs(path=f"{entity}/{wandb_project}", per_page=1000)

    results: list[RunInfo] = []
    for run in runs:
        tags_dict = dict(run.config)
        tags_dict["wandb_tags"] = ",".join(run.tags) if run.tags else ""
        results.append(RunInfo(
            run_id=run.id,
            status=run.state,
            start_time=run.created_at or "",
            end_time=run.heartbeat_at,
            tags=tags_dict,
            metrics=dict(run.summary) if run.summary else {},
            is_deleted=(run.state == "deleted"),
        ))
    return results


def load_runs_local(runs_dir: Path) -> list[RunInfo]:
    """Load runs from local JSON files."""
    results: list[RunInfo] = []
    if not runs_dir.exists():
        return results

    for f in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            results.append(RunInfo(
                run_id=data.get("run_id", f.stem),
                status=data.get("status", "unknown"),
                start_time=data.get("start_time", ""),
                end_time=data.get("end_time"),
                tags=data.get("tags", {}),
                metrics=data.get("metrics", {}),
                is_deleted=data.get("is_deleted", False),
            ))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: Skipping {f.name}: {e}", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_deleted_runs(runs: list[RunInfo]) -> CheckResult:
    """Check 1: No runs have been deleted."""
    deleted = [r for r in runs if r.is_deleted]
    total = len(runs)

    if deleted:
        return CheckResult(
            "Deleted Runs",
            False,
            f"{len(deleted)} runs deleted out of {total} total. NEVER delete runs.",
        )
    return CheckResult(
        "Deleted Runs",
        True,
        f"All {total} runs preserved. No deletions detected.",
    )


def check_holdout_count(runs: list[RunInfo]) -> CheckResult:
    """Check 2: At most 1 hold-out run exists."""
    holdout_runs = [r for r in runs if r.is_holdout]

    if len(holdout_runs) > 1:
        ids = [r.run_id[:8] for r in holdout_runs]
        return CheckResult(
            "Hold-out Count",
            False,
            f"{len(holdout_runs)} hold-out runs found ({ids}). "
            "Hold-out is ONE-SHOT (max 1 run).",
        )
    return CheckResult(
        "Hold-out Count",
        True,
        f"{len(holdout_runs)} hold-out run(s) found. Within limit.",
    )


def check_gate_conditions(
    runs: list[RunInfo],
    project_dir: Path,
) -> CheckResult:
    """Check 3: CV gate met before hold-out run."""
    holdout_runs = [r for r in runs if r.is_holdout]
    if not holdout_runs:
        return CheckResult(
            "Gate Conditions",
            True,
            "No hold-out run found. Gate check not applicable.",
        )

    # Parse gate conditions from 02_METRICS.md
    metrics_path = project_dir / "docs" / "specs" / "02_METRICS.md"
    gate_metric = None
    gate_threshold = None

    if metrics_path.exists():
        text = metrics_path.read_text()
        # Look for patterns like "AUC >= 0.80" or "accuracy > 0.75"
        gate_match = re.search(
            r'(\w+)\s*(>=?|<=?)\s*([\d.]+)', text
        )
        if gate_match:
            gate_metric = gate_match.group(1).lower()
            gate_op = gate_match.group(2)
            gate_threshold = float(gate_match.group(3))

    if not gate_metric:
        return CheckResult(
            "Gate Conditions",
            True,
            "No gate conditions found in 02_METRICS.md. Skipping.",
        )

    holdout_run = holdout_runs[0]
    holdout_time = holdout_run.start_datetime

    # Find CV runs that meet gate before hold-out
    cv_runs = [r for r in runs if not r.is_holdout and not r.is_deleted]
    gate_met = False
    for r in cv_runs:
        r_time = r.start_datetime
        metric_val = r.metrics.get(gate_metric)
        if metric_val is None:
            continue
        if r_time and holdout_time and r_time >= holdout_time:
            continue
        if ">=" in gate_op and metric_val >= gate_threshold:
            gate_met = True
            break
        if ">" in gate_op and metric_val > gate_threshold:
            gate_met = True
            break

    if not gate_met:
        return CheckResult(
            "Gate Conditions",
            False,
            f"Hold-out run at {holdout_run.start_time} but no CV run meets "
            f"gate ({gate_metric} {gate_op} {gate_threshold}) before that date.",
        )
    return CheckResult(
        "Gate Conditions",
        True,
        f"CV gate ({gate_metric} >= {gate_threshold}) met before hold-out.",
    )


def check_pre_registration_timing(
    runs: list[RunInfo],
    project_dir: Path,
) -> CheckResult:
    """Check 4: Hypotheses committed before first experiment run."""
    hyp_path = project_dir / "docs" / "specs" / "00_HYPOTHESES.md"

    if not hyp_path.exists():
        return CheckResult(
            "Pre-Registration Timing",
            False,
            "00_HYPOTHESES.md not found. Pre-registration required.",
        )

    # Get git timestamp of first commit of 00_HYPOTHESES.md
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%aI", "--diff-filter=A", "--", str(hyp_path)],
            capture_output=True, text=True,
            cwd=str(project_dir),
        )
        git_dates = result.stdout.strip().splitlines()
        if not git_dates:
            # Fallback: get earliest commit
            result = subprocess.run(
                ["git", "log", "--follow", "--format=%aI", "--reverse", "--", str(hyp_path)],
                capture_output=True, text=True,
                cwd=str(project_dir),
            )
            git_dates = result.stdout.strip().splitlines()
    except FileNotFoundError:
        return CheckResult(
            "Pre-Registration Timing",
            True,
            "Git not available. Cannot verify timing. Manual check required.",
        )

    if not git_dates:
        return CheckResult(
            "Pre-Registration Timing",
            False,
            "00_HYPOTHESES.md exists but has no git history. Commit it first.",
        )

    hyp_date_str = git_dates[-1] if git_dates else git_dates[0]
    try:
        hyp_date = datetime.fromisoformat(hyp_date_str)
    except ValueError:
        hyp_date = None

    # Get first run timestamp
    active_runs = [r for r in runs if not r.is_deleted and r.start_datetime]
    if not active_runs:
        return CheckResult(
            "Pre-Registration Timing",
            True,
            "No experiment runs found. Timing check not applicable.",
        )

    first_run = min(active_runs, key=lambda r: r.start_datetime)
    first_run_time = first_run.start_datetime

    if hyp_date and first_run_time:
        if hyp_date.replace(tzinfo=None) > first_run_time:
            return CheckResult(
                "Pre-Registration Timing",
                False,
                f"First run at {first_run.start_time} but 00_HYPOTHESES.md "
                f"committed at {hyp_date_str}. Hypotheses must precede experiments.",
            )

    return CheckResult(
        "Pre-Registration Timing",
        True,
        f"00_HYPOTHESES.md committed at {hyp_date_str}, "
        f"first run at {first_run.start_time}. Order correct.",
    )


def check_spec_drift(
    runs: list[RunInfo],
    project_dir: Path,
) -> CheckResult:
    """Check 5: No undocumented post-experiment spec changes."""
    specs_dir = project_dir / "docs" / "specs"
    if not specs_dir.exists():
        return CheckResult(
            "Spec Drift",
            False,
            "docs/specs/ directory not found.",
        )

    # Get first run timestamp
    active_runs = [r for r in runs if not r.is_deleted and r.start_datetime]
    if not active_runs:
        return CheckResult(
            "Spec Drift",
            True,
            "No experiment runs found. Drift check not applicable.",
        )

    first_run = min(active_runs, key=lambda r: r.start_datetime)
    first_run_time = first_run.start_datetime

    # Get git log for spec files
    try:
        result = subprocess.run(
            ["git", "log", "--format=%aI %s", "--name-only", "--", "docs/specs/"],
            capture_output=True, text=True,
            cwd=str(project_dir),
        )
    except FileNotFoundError:
        return CheckResult(
            "Spec Drift",
            True,
            "Git not available. Cannot check spec drift.",
        )

    # Parse git log for post-experiment changes
    post_changes: list[str] = []
    current_date = None
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        # Try to parse as date line
        if line[0].isdigit() and "T" in line[:25]:
            parts = line.split(" ", 1)
            try:
                current_date = datetime.fromisoformat(parts[0])
            except ValueError:
                current_date = None
        elif current_date and line.endswith(".md"):
            if first_run_time and current_date.replace(tzinfo=None) > first_run_time:
                post_changes.append(f"{line} ({current_date.date()})")

    if not post_changes:
        return CheckResult(
            "Spec Drift",
            True,
            "No spec changes after first experiment run.",
        )

    # Check if changes are documented in Deviation Log
    hyp_path = project_dir / "docs" / "specs" / "00_HYPOTHESES.md"
    deviation_log = ""
    if hyp_path.exists():
        text = hyp_path.read_text()
        # Extract deviation log section
        log_match = re.search(
            r'(?:##\s*Deviation\s*Log|##\s*Deviations)(.*?)(?=\n##|\Z)',
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if log_match:
            deviation_log = log_match.group(1)

    undocumented = []
    for change in post_changes:
        filename = change.split(" (")[0]
        if filename not in deviation_log:
            undocumented.append(change)

    if undocumented:
        return CheckResult(
            "Spec Drift",
            False,
            f"{len(undocumented)} post-experiment spec change(s) not in Deviation Log: "
            + "; ".join(undocumented[:3]),
        )

    return CheckResult(
        "Spec Drift",
        True,
        f"{len(post_changes)} post-experiment spec change(s), all documented in Deviation Log.",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment Audit: 5 checks for experiment integrity"
    )
    parser.add_argument(
        "--project-dir", type=Path, required=True,
        help="Root directory of the SDD ML project",
    )
    parser.add_argument(
        "--backend", choices=["mlflow", "wandb", "local"],
        default="local",
        help="Experiment tracking backend",
    )
    parser.add_argument(
        "--tracking-uri", type=str, default="http://localhost:5000",
        help="MLflow tracking URI",
    )
    parser.add_argument(
        "--experiment-name", type=str, default=None,
        help="MLflow experiment name",
    )
    parser.add_argument(
        "--entity", type=str, default=None,
        help="W&B entity (team/user)",
    )
    parser.add_argument(
        "--wandb-project", type=str, default=None,
        help="W&B project name",
    )
    parser.add_argument(
        "--runs-dir", type=Path, default=None,
        help="Local runs directory (for local backend)",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()

    # Load runs from backend
    runs: list[RunInfo] = []
    if args.backend == "mlflow":
        if not args.experiment_name:
            print("ERROR: --experiment-name required for mlflow backend", file=sys.stderr)
            sys.exit(1)
        runs = load_runs_mlflow(args.tracking_uri, args.experiment_name)
    elif args.backend == "wandb":
        if not args.entity or not args.wandb_project:
            print("ERROR: --entity and --wandb-project required for wandb backend", file=sys.stderr)
            sys.exit(1)
        runs = load_runs_wandb(args.entity, args.wandb_project)
    elif args.backend == "local":
        runs_dir = args.runs_dir or (project_dir / "data" / "processed" / "runs")
        runs = load_runs_local(runs_dir)

    results: list[CheckResult] = [
        check_deleted_runs(runs),
        check_holdout_count(runs),
        check_gate_conditions(runs, project_dir),
        check_pre_registration_timing(runs, project_dir),
        check_spec_drift(runs, project_dir),
    ]

    # Report
    print("\n=== Experiment Audit Report ===\n")
    all_passed = True
    for r in results:
        print(r)
        if not r.passed:
            all_passed = False

    print(f"\n{'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
