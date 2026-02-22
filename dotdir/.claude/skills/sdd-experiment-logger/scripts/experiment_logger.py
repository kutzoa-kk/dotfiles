#!/usr/bin/env python3
"""
Experiment Logger for SDD ML Projects.

Generates per-experiment markdown logs and a comparison matrix,
linked to MLflow run_name for traceability.

Usage:
    # Create experiment log for a specific run
    python experiment_logger.py --project-dir /path/to/project \\
        --run-name baseline-v1 \\
        --runs-json data/processed/all_runs.json

    # Generate comparison matrix from all experiment logs
    python experiment_logger.py --project-dir /path/to/project \\
        --runs-json data/processed/all_runs.json \\
        --generate-comparison

    # Update a specific section of an existing log
    python experiment_logger.py --project-dir /path/to/project \\
        --run-name baseline-v1 \\
        --update-section observations \\
        --content "Fold 3 showed overfitting after epoch 15"
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


EXPERIMENTS_DIR = "docs/experiments"
COMPARISON_FILE = "COMPARISON.md"


# ---------------------------------------------------------------------------
# Gate Condition Extraction
# ---------------------------------------------------------------------------

def _extract_gate_conditions(project_dir: Path) -> list[dict]:
    """Extract gate conditions from 02_METRICS.md."""
    metrics_path = project_dir / "docs" / "specs" / "02_METRICS.md"
    if not metrics_path.exists():
        return []

    text = metrics_path.read_text()
    gates: list[dict] = []
    for match in re.finditer(r'(\w+)\s*(>=?|<=?)\s*([\d.]+)', text):
        gates.append({
            "metric": match.group(1).lower(),
            "operator": match.group(2),
            "threshold": float(match.group(3)),
            "display": f"{match.group(1)} {match.group(2)} {match.group(3)}",
        })
    return gates


def _check_gate(value: Optional[float], operator: str, threshold: float) -> bool:
    """Check if a value meets a gate condition."""
    if value is None:
        return False
    if ">=" in operator:
        return value >= threshold
    if ">" in operator:
        return value > threshold
    if "<=" in operator:
        return value <= threshold
    if "<" in operator:
        return value < threshold
    return False


# ---------------------------------------------------------------------------
# Run Lookup
# ---------------------------------------------------------------------------

def _find_run_by_name(runs: list[dict], run_name: str) -> Optional[dict]:
    """Find a run record by run_name, falling back to run_id prefix match."""
    for r in runs:
        if r.get("run_name") == run_name:
            return r
    for r in runs:
        if r.get("run_id", "").startswith(run_name):
            return r
    return None


def _get_sorted_runs(runs: list[dict]) -> list[dict]:
    """Return runs sorted by start_time ascending."""
    def sort_key(r: dict) -> str:
        return r.get("start_time", "") or ""
    return sorted(runs, key=sort_key)


def _find_previous_run(runs: list[dict], current_run: dict) -> Optional[dict]:
    """Find the run immediately before the current one by start_time."""
    sorted_runs = _get_sorted_runs(runs)
    current_time = current_run.get("start_time", "")
    prev = None
    for r in sorted_runs:
        if r.get("run_name") == current_run.get("run_name"):
            break
        prev = r
    return prev


# ---------------------------------------------------------------------------
# Experiment Log Generation
# ---------------------------------------------------------------------------

def create_experiment_log(
    run_name: str,
    run_data: dict,
    project_dir: Path,
    gate_conditions: list[dict],
) -> Path:
    """Create a per-experiment markdown log."""
    experiments_dir = project_dir / EXPERIMENTS_DIR
    experiments_dir.mkdir(parents=True, exist_ok=True)

    run_id = run_data.get("run_id", "unknown")
    phase = run_data.get("phase", "cv")
    status = run_data.get("status", "unknown")
    start_time = run_data.get("start_time", "N/A")
    end_time = run_data.get("end_time", "N/A") or "N/A"
    metrics = run_data.get("metrics", {})
    params = run_data.get("params", {})

    lines: list[str] = []

    # Header
    lines.append(f"# Experiment: {run_name}")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Run ID | `{run_id}` |")
    lines.append(f"| Run Name | {run_name} |")
    lines.append(f"| Phase | {phase} |")
    lines.append(f"| Status | {status} |")
    lines.append(f"| Started | {start_time} |")
    lines.append(f"| Completed | {end_time} |")
    lines.append("")

    # Objective (placeholder for LLM)
    lines.append("## Objective")
    lines.append("")
    lines.append("<!-- Describe the hypothesis or goal for this experiment -->")
    lines.append("")

    # Configuration
    lines.append("## Configuration")
    lines.append("")
    if params:
        lines.append("| Parameter | Value |")
        lines.append("|-----------|-------|")
        for k, v in sorted(params.items()):
            lines.append(f"| {k} | {v} |")
    else:
        lines.append("*No parameters recorded.*")
    lines.append("")

    # Results
    lines.append("## Results")
    lines.append("")
    if metrics:
        lines.append("| Metric | Value | Gate | Status |")
        lines.append("|--------|-------|------|--------|")
        for k, v in sorted(metrics.items()):
            gate_info = ""
            gate_status = ""
            for g in gate_conditions:
                if g["metric"] == k.lower():
                    gate_info = g["display"]
                    met = _check_gate(
                        float(v) if isinstance(v, (int, float)) else None,
                        g["operator"],
                        g["threshold"],
                    )
                    gate_status = "PASS" if met else "FAIL"
                    break
            val_str = f"{v:.6f}" if isinstance(v, float) else str(v)
            lines.append(f"| {k} | {val_str} | {gate_info} | {gate_status} |")
    else:
        lines.append("*No metrics recorded.*")
    lines.append("")

    # Observations (placeholder for LLM)
    lines.append("## Observations")
    lines.append("")
    lines.append("### What Worked")
    lines.append("")
    lines.append("<!-- Describe what produced positive results -->")
    lines.append("")
    lines.append("### What Didn't Work")
    lines.append("")
    lines.append("<!-- Describe what did not meet expectations -->")
    lines.append("")
    lines.append("### Unexpected Findings")
    lines.append("")
    lines.append("<!-- Note any surprising observations -->")
    lines.append("")

    # Next Steps (placeholder for LLM)
    lines.append("## Next Steps")
    lines.append("")
    lines.append("- [ ] <!-- Suggested follow-up experiment or action -->")
    lines.append("")

    # Related Experiments
    lines.append("## Related Experiments")
    lines.append("")
    lines.append("<!-- Link to previous/next experiments -->")
    lines.append("")

    output_path = experiments_dir / f"{run_name}.md"
    output_path.write_text("\n".join(lines))
    return output_path


# ---------------------------------------------------------------------------
# Experiment Log Update
# ---------------------------------------------------------------------------

SECTION_MARKERS = {
    "objective": "## Objective",
    "observations": "## Observations",
    "next_steps": "## Next Steps",
    "next-steps": "## Next Steps",
    "related": "## Related Experiments",
}


def _parse_experiment_log(path: Path) -> dict[str, str]:
    """Parse an experiment log into sections keyed by heading."""
    text = path.read_text()
    sections: dict[str, str] = {}
    current_key = "_header"
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            sections[current_key] = "\n".join(current_lines)
            current_key = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_key] = "\n".join(current_lines)
    return sections


def update_experiment_log(
    run_name: str,
    project_dir: Path,
    section: str,
    content: str,
) -> None:
    """Update a specific section of an existing experiment log."""
    experiments_dir = project_dir / EXPERIMENTS_DIR
    log_path = experiments_dir / f"{run_name}.md"

    if not log_path.exists():
        print(f"ERROR: Log not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    marker = SECTION_MARKERS.get(section.lower())
    if not marker:
        print(
            f"ERROR: Unknown section '{section}'. "
            f"Valid: {', '.join(SECTION_MARKERS.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    sections = _parse_experiment_log(log_path)
    if marker not in sections:
        print(f"ERROR: Section '{marker}' not found in {log_path}", file=sys.stderr)
        sys.exit(1)

    sections[marker] = f"\n{content}\n"

    # Reconstruct file
    lines: list[str] = []
    for key, body in sections.items():
        if key == "_header":
            lines.append(body)
        else:
            lines.append(key)
            lines.append(body)

    log_path.write_text("\n".join(lines))
    print(f"Updated section '{section}' in {log_path}")


# ---------------------------------------------------------------------------
# Comparison Matrix
# ---------------------------------------------------------------------------

def generate_comparison_matrix(
    project_dir: Path,
    runs_data: dict,
) -> Path:
    """Generate a comparison matrix from all experiment logs and run data."""
    experiments_dir = project_dir / EXPERIMENTS_DIR
    experiments_dir.mkdir(parents=True, exist_ok=True)

    runs = runs_data.get("runs", [])
    gate_conditions = _extract_gate_conditions(project_dir)

    # Determine primary metric from gate conditions
    primary_metric = gate_conditions[0]["metric"] if gate_conditions else None

    lines: list[str] = []
    lines.append("# Experiment Comparison Matrix")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Total Runs**: {len(runs)}")
    lines.append("")

    # Main comparison table
    lines.append("## Run Comparison")
    lines.append("")
    lines.append("| Run Name | Phase | Status | Primary Metric | Key Change | Outcome |")
    lines.append("|----------|-------|--------|---------------|------------|---------|")

    sorted_runs = _get_sorted_runs(runs)
    prev_run: Optional[dict] = None

    for r in sorted_runs:
        if r.get("is_deleted"):
            continue

        run_name = r.get("run_name", r.get("run_id", "unknown")[:8])
        phase = r.get("phase", "cv")
        status = r.get("status", "unknown")
        metrics = r.get("metrics", {})

        primary_val = ""
        if primary_metric:
            for k, v in metrics.items():
                if k.lower() == primary_metric:
                    primary_val = f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
                    break

        # Detect key change vs previous run
        key_change = _detect_key_change(r, prev_run) if prev_run else "Initial run"

        # Determine outcome based on gate
        outcome = ""
        if primary_metric and primary_val:
            for g in gate_conditions:
                if g["metric"] == primary_metric:
                    met = _check_gate(
                        float(primary_val) if primary_val else None,
                        g["operator"],
                        g["threshold"],
                    )
                    outcome = "PASS" if met else "FAIL"
                    break

        log_link = f"[{run_name}](./{run_name}.md)"
        lines.append(
            f"| {log_link} | {phase} | {status} | "
            f"{primary_val} | {key_change} | {outcome} |"
        )
        prev_run = r

    lines.append("")

    # Effective / Ineffective techniques (placeholders for LLM)
    lines.append("## Effective Techniques")
    lines.append("")
    lines.append("<!-- List techniques that consistently improved metrics -->")
    lines.append("")
    lines.append("## Ineffective Techniques")
    lines.append("")
    lines.append("<!-- List techniques that did not improve or hurt metrics -->")
    lines.append("")

    # Current best model
    lines.append("## Current Best Model")
    lines.append("")
    if sorted_runs and primary_metric:
        best_run = _find_best_run(sorted_runs, primary_metric)
        if best_run:
            best_name = best_run.get("run_name", best_run.get("run_id", "unknown")[:8])
            best_val = ""
            for k, v in best_run.get("metrics", {}).items():
                if k.lower() == primary_metric:
                    best_val = f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
                    break
            lines.append(f"**Run**: [{best_name}](./{best_name}.md)")
            lines.append(f"**{primary_metric}**: {best_val}")
        else:
            lines.append("*No runs with primary metric found.*")
    else:
        lines.append("*No gate conditions defined to determine primary metric.*")
    lines.append("")

    # Recommended next experiments
    lines.append("## Recommended Next Experiments")
    lines.append("")
    lines.append("<!-- Based on the patterns observed, suggest next experiments -->")
    lines.append("")

    output_path = experiments_dir / COMPARISON_FILE
    output_path.write_text("\n".join(lines))
    return output_path


def _detect_key_change(current: dict, previous: dict) -> str:
    """Detect the primary difference between two runs based on params."""
    curr_params = current.get("params", {})
    prev_params = previous.get("params", {})

    changes: list[str] = []
    all_keys = set(curr_params.keys()) | set(prev_params.keys())

    for k in sorted(all_keys):
        curr_val = curr_params.get(k)
        prev_val = prev_params.get(k)
        if curr_val != prev_val:
            if prev_val is None:
                changes.append(f"+{k}={curr_val}")
            elif curr_val is None:
                changes.append(f"-{k}")
            else:
                changes.append(f"{k}: {prev_val}->{curr_val}")

    if not changes:
        return "No param changes"
    return "; ".join(changes[:3])


def _find_best_run(runs: list[dict], metric_name: str) -> Optional[dict]:
    """Find the run with the best (max) value for a metric."""
    best_run = None
    best_val = float("-inf")
    for r in runs:
        if r.get("is_deleted"):
            continue
        for k, v in r.get("metrics", {}).items():
            if k.lower() == metric_name and isinstance(v, (int, float)):
                if v > best_val:
                    best_val = v
                    best_run = r
    return best_run


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment Logger: create, update, and compare experiment logs"
    )
    parser.add_argument(
        "--project-dir", type=Path, required=True,
        help="Root directory of the SDD ML project",
    )
    parser.add_argument(
        "--run-name", type=str, default=None,
        help="Run name to create or update a log for",
    )
    parser.add_argument(
        "--runs-json", type=Path, default=None,
        help="Path to all_runs.json (default: data/processed/all_runs.json)",
    )
    parser.add_argument(
        "--generate-comparison", action="store_true",
        help="Generate comparison matrix from all runs",
    )
    parser.add_argument(
        "--update-section", type=str, default=None,
        help="Section to update (objective, observations, next_steps, related)",
    )
    parser.add_argument(
        "--content", type=str, default=None,
        help="Content for section update",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    runs_json = args.runs_json or (project_dir / "data" / "processed" / "all_runs.json")

    # Update section mode
    if args.update_section:
        if not args.run_name:
            print("ERROR: --run-name required with --update-section", file=sys.stderr)
            sys.exit(1)
        if not args.content:
            print("ERROR: --content required with --update-section", file=sys.stderr)
            sys.exit(1)
        update_experiment_log(args.run_name, project_dir, args.update_section, args.content)
        return

    # Load runs data
    if not runs_json.exists():
        print(f"ERROR: {runs_json} not found. Run collect_runs.py first.", file=sys.stderr)
        sys.exit(1)

    runs_data = json.loads(runs_json.read_text())
    runs = runs_data.get("runs", [])

    # Generate comparison mode
    if args.generate_comparison:
        path = generate_comparison_matrix(project_dir, runs_data)
        print(f"Comparison matrix generated: {path}")
        return

    # Create experiment log mode
    if not args.run_name:
        print("ERROR: --run-name or --generate-comparison required", file=sys.stderr)
        sys.exit(1)

    run_data = _find_run_by_name(runs, args.run_name)
    if not run_data:
        print(
            f"ERROR: Run '{args.run_name}' not found in {runs_json}. "
            f"Available: {[r.get('run_name', r.get('run_id', '')[:8]) for r in runs[:10]]}",
            file=sys.stderr,
        )
        sys.exit(1)

    gate_conditions = _extract_gate_conditions(project_dir)
    path = create_experiment_log(args.run_name, run_data, project_dir, gate_conditions)
    print(f"Experiment log created: {path}")

    # Also link previous experiment if found
    prev = _find_previous_run(runs, run_data)
    if prev:
        prev_name = prev.get("run_name", prev.get("run_id", "")[:8])
        prev_log = project_dir / EXPERIMENTS_DIR / f"{prev_name}.md"
        if prev_log.exists():
            print(f"Previous experiment: {prev_name} ({prev_log})")


if __name__ == "__main__":
    main()
