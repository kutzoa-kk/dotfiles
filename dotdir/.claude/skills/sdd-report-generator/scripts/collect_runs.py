#!/usr/bin/env python3
"""
Run Collector for SDD ML Projects.

Collects all experiment runs from MLflow/W&B/local backend,
computes summary statistics, and outputs JSON for report generation.

Usage:
    python collect_runs.py \\
        --project-dir /path/to/project \\
        --backend mlflow \\
        --tracking-uri http://localhost:5000 \\
        --experiment-name my-experiment \\
        --output data/processed/all_runs.json
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class RunRecord:
    """Immutable experiment run record for report generation."""

    def __init__(
        self,
        run_id: str,
        status: str,
        start_time: str,
        end_time: Optional[str],
        tags: dict[str, str],
        metrics: dict[str, float],
        params: dict[str, str],
        is_deleted: bool,
        phase: str,
    ):
        self.run_id = run_id
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.tags = tags
        self.metrics = metrics
        self.params = params
        self.is_deleted = is_deleted
        self.phase = phase

    def to_dict(self) -> dict:
        """Convert to serializable dictionary."""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "tags": self.tags,
            "metrics": self.metrics,
            "params": self.params,
            "is_deleted": self.is_deleted,
            "phase": self.phase,
        }


def _classify_phase(tags: dict[str, str]) -> str:
    """Determine run phase from tags."""
    phase = tags.get("phase", "").lower()
    if phase in ("holdout", "hold-out", "hold_out"):
        return "holdout"
    if phase in ("exploratory", "exploration"):
        return "exploratory"
    if tags.get("holdout", "").lower() == "true":
        return "holdout"
    return "cv"


# ---------------------------------------------------------------------------
# Backend Loaders
# ---------------------------------------------------------------------------

def collect_from_mlflow(
    tracking_uri: str,
    experiment_name: str,
) -> list[RunRecord]:
    """Collect runs from MLflow."""
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

    records: list[RunRecord] = []
    for run in all_runs:
        tags = dict(run.data.tags)
        start_ms = run.info.start_time
        end_ms = run.info.end_time
        records.append(RunRecord(
            run_id=run.info.run_id,
            status=run.info.status,
            start_time=datetime.fromtimestamp(start_ms / 1000).isoformat() if start_ms else "",
            end_time=datetime.fromtimestamp(end_ms / 1000).isoformat() if end_ms else None,
            tags=tags,
            metrics=dict(run.data.metrics),
            params=dict(run.data.params),
            is_deleted=(run.info.lifecycle_stage == "deleted"),
            phase=_classify_phase(tags),
        ))
    return records


def collect_from_wandb(
    entity: str,
    wandb_project: str,
) -> list[RunRecord]:
    """Collect runs from W&B."""
    try:
        import wandb
    except ImportError:
        print("ERROR: wandb not installed. Run: pip install wandb", file=sys.stderr)
        sys.exit(1)

    api = wandb.Api()
    runs = api.runs(path=f"{entity}/{wandb_project}", per_page=1000)

    records: list[RunRecord] = []
    for run in runs:
        tags_dict = dict(run.config)
        tags_dict["wandb_tags"] = ",".join(run.tags) if run.tags else ""
        records.append(RunRecord(
            run_id=run.id,
            status=run.state,
            start_time=run.created_at or "",
            end_time=run.heartbeat_at,
            tags=tags_dict,
            metrics={k: v for k, v in (run.summary or {}).items() if isinstance(v, (int, float))},
            params=dict(run.config),
            is_deleted=(run.state == "deleted"),
            phase=_classify_phase(tags_dict),
        ))
    return records


def collect_from_local(runs_dir: Path) -> list[RunRecord]:
    """Collect runs from local JSON files."""
    records: list[RunRecord] = []
    if not runs_dir.exists():
        return records

    for f in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            tags = data.get("tags", {})
            records.append(RunRecord(
                run_id=data.get("run_id", f.stem),
                status=data.get("status", "unknown"),
                start_time=data.get("start_time", ""),
                end_time=data.get("end_time"),
                tags=tags,
                metrics=data.get("metrics", {}),
                params=data.get("params", {}),
                is_deleted=data.get("is_deleted", False),
                phase=_classify_phase(tags),
            ))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: Skipping {f.name}: {e}", file=sys.stderr)
    return records


# ---------------------------------------------------------------------------
# Summary Statistics
# ---------------------------------------------------------------------------

def compute_summary(records: list[RunRecord]) -> dict:
    """Compute summary statistics from run records."""
    total = len(records)
    deleted = sum(1 for r in records if r.is_deleted)
    failed = sum(1 for r in records if r.status in ("FAILED", "failed", "crashed"))
    cv_runs = [r for r in records if r.phase == "cv" and not r.is_deleted]
    holdout_runs = [r for r in records if r.phase == "holdout" and not r.is_deleted]

    # Collect all metric names from non-deleted runs
    active_runs = [r for r in records if not r.is_deleted]
    all_metrics: dict[str, list[float]] = {}
    for r in active_runs:
        for k, v in r.metrics.items():
            if isinstance(v, (int, float)) and not math.isnan(v):
                all_metrics.setdefault(k, []).append(float(v))

    metric_stats: list[dict] = []
    for name, values in sorted(all_metrics.items()):
        if not values:
            continue
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n if n > 1 else 0.0
        std = math.sqrt(variance)
        metric_stats.append({
            "name": name,
            "mean": round(mean, 6),
            "std": round(std, 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "n": n,
        })

    return {
        "total_run_count": total,
        "deleted_run_count": deleted,
        "failed_run_count": failed,
        "cv_run_count": len(cv_runs),
        "holdout_run_count": len(holdout_runs),
        "metric_stats": metric_stats,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect experiment runs and compute summary statistics"
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
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output JSON path (default: data/processed/all_runs.json)",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()

    # Collect runs
    records: list[RunRecord] = []
    if args.backend == "mlflow":
        if not args.experiment_name:
            print("ERROR: --experiment-name required for mlflow backend", file=sys.stderr)
            sys.exit(1)
        records = collect_from_mlflow(args.tracking_uri, args.experiment_name)
    elif args.backend == "wandb":
        if not args.entity or not args.wandb_project:
            print("ERROR: --entity and --wandb-project required for wandb", file=sys.stderr)
            sys.exit(1)
        records = collect_from_wandb(args.entity, args.wandb_project)
    elif args.backend == "local":
        runs_dir = args.runs_dir or (project_dir / "data" / "processed" / "runs")
        records = collect_from_local(runs_dir)

    # Compute summary
    summary = compute_summary(records)

    # Build output
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "backend": args.backend,
        "summary": summary,
        "runs": [r.to_dict() for r in records],
    }

    # Write output
    output_path = args.output or (project_dir / "data" / "processed" / "all_runs.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))

    print(f"Collected {len(records)} runs.")
    print(f"Summary: {summary['cv_run_count']} CV, "
          f"{summary['holdout_run_count']} holdout, "
          f"{summary['deleted_run_count']} deleted, "
          f"{summary['failed_run_count']} failed")
    print(f"Output: {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
