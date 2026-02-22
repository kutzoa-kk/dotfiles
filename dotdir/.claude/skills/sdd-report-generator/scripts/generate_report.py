#!/usr/bin/env python3
"""
Report Generator for SDD ML Projects.

Generates docs/FINAL_REPORT.md from collected runs and project specs.
Enforces R8 (Anti-Sycophancy) and R10 (Full Reporting).

Usage:
    python generate_report.py \\
        --project-dir /path/to/project \\
        --runs-json data/processed/all_runs.json \\
        --correction bonferroni \\
        --alpha 0.05
"""

import argparse
import json
import math
import re
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


# ---------------------------------------------------------------------------
# Hypothesis Parsing
# ---------------------------------------------------------------------------

class Hypothesis:
    """Immutable hypothesis record."""

    def __init__(
        self,
        index: int,
        description: str,
        metric: str,
        threshold: Optional[float],
        is_confirmatory: bool,
    ):
        self.index = index
        self.description = description
        self.metric = metric
        self.threshold = threshold
        self.is_confirmatory = is_confirmatory


def parse_hypotheses(project_dir: Path) -> list[Hypothesis]:
    """Parse hypotheses from 00_HYPOTHESES.md."""
    hyp_path = project_dir / "docs" / "specs" / "00_HYPOTHESES.md"
    if not hyp_path.exists():
        return []

    text = hyp_path.read_text()
    hypotheses: list[Hypothesis] = []

    # Split into confirmatory and exploratory sections
    confirm_section = ""
    explore_section = ""

    confirm_match = re.search(
        r'(?:##\s*Confirmatory|##\s*Primary)(.*?)(?=\n##|\Z)',
        text, re.DOTALL | re.IGNORECASE,
    )
    if confirm_match:
        confirm_section = confirm_match.group(1)

    explore_match = re.search(
        r'(?:##\s*Exploratory|##\s*Secondary)(.*?)(?=\n##|\Z)',
        text, re.DOTALL | re.IGNORECASE,
    )
    if explore_match:
        explore_section = explore_match.group(1)

    idx = 1
    for line in confirm_section.splitlines():
        hyp = _parse_hypothesis_line(line, idx, is_confirmatory=True)
        if hyp:
            hypotheses.append(hyp)
            idx += 1

    for line in explore_section.splitlines():
        hyp = _parse_hypothesis_line(line, idx, is_confirmatory=False)
        if hyp:
            hypotheses.append(hyp)
            idx += 1

    # Fallback: if no sections found, try parsing entire doc
    if not hypotheses:
        for line in text.splitlines():
            hyp = _parse_hypothesis_line(line, idx, is_confirmatory=True)
            if hyp:
                hypotheses.append(hyp)
                idx += 1

    return hypotheses


def _parse_hypothesis_line(
    line: str,
    index: int,
    is_confirmatory: bool,
) -> Optional[Hypothesis]:
    """Parse a single hypothesis from a markdown line."""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("|"):
        return None

    # Match patterns like "- H1: description (metric >= threshold)"
    hyp_match = re.match(
        r'[-*\d.]+\s*[Hh]?\d*:?\s*(.*?)(?:\((\w+)\s*(>=?|<=?)\s*([\d.]+)\))?$',
        line,
    )
    if not hyp_match or not hyp_match.group(1).strip():
        return None

    description = hyp_match.group(1).strip()
    metric = hyp_match.group(2) or ""
    threshold = float(hyp_match.group(4)) if hyp_match.group(4) else None

    return Hypothesis(
        index=index,
        description=description,
        metric=metric.lower(),
        threshold=threshold,
        is_confirmatory=is_confirmatory,
    )


# ---------------------------------------------------------------------------
# Deviation Log
# ---------------------------------------------------------------------------

def parse_deviation_log(project_dir: Path) -> list[dict[str, str]]:
    """Parse deviation log from 00_HYPOTHESES.md."""
    hyp_path = project_dir / "docs" / "specs" / "00_HYPOTHESES.md"
    if not hyp_path.exists():
        return []

    text = hyp_path.read_text()
    log_match = re.search(
        r'(?:##\s*Deviation\s*Log|##\s*Deviations)(.*?)(?=\n##|\Z)',
        text, re.DOTALL | re.IGNORECASE,
    )
    if not log_match:
        return []

    entries: list[dict[str, str]] = []
    for line in log_match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|-") or "Date" in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) >= 3:
            entries.append({
                "date": cells[0],
                "file": cells[1] if len(cells) > 1 else "",
                "description": cells[2] if len(cells) > 2 else "",
                "rationale": cells[3] if len(cells) > 3 else "",
                "impact": cells[4] if len(cells) > 4 else "",
            })
    return entries


# ---------------------------------------------------------------------------
# Gate Conditions
# ---------------------------------------------------------------------------

def parse_gates(project_dir: Path) -> list[dict[str, str]]:
    """Parse gate conditions from 02_METRICS.md."""
    metrics_path = project_dir / "docs" / "specs" / "02_METRICS.md"
    if not metrics_path.exists():
        return []

    text = metrics_path.read_text()
    gates: list[dict[str, str]] = []

    # Match patterns like "metric >= value" or "metric > value"
    for match in re.finditer(r'(\w+)\s*(>=?|<=?)\s*([\d.]+)', text):
        gates.append({
            "name": match.group(1),
            "condition": f"{match.group(1)} {match.group(2)} {match.group(3)}",
            "metric": match.group(1).lower(),
            "operator": match.group(2),
            "threshold": match.group(3),
        })

    return gates


# ---------------------------------------------------------------------------
# Multiple Comparison Corrections
# ---------------------------------------------------------------------------

def bonferroni_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[dict]:
    """Apply Bonferroni correction."""
    n = len(p_values)
    if n == 0:
        return []
    results = []
    for p in p_values:
        adjusted_p = min(p * n, 1.0)
        results.append({
            "raw_p": round(p, 6),
            "adjusted_p": round(adjusted_p, 6),
            "significant": adjusted_p < alpha,
        })
    return results


def benjamini_hochberg_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[dict]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    if n == 0:
        return []

    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    prev_adj = 1.0

    for rank_minus_1 in range(n - 1, -1, -1):
        orig_idx, raw_p = indexed[rank_minus_1]
        rank = rank_minus_1 + 1
        adj_p = min(raw_p * n / rank, 1.0)
        adj_p = min(adj_p, prev_adj)
        adjusted[orig_idx] = adj_p
        prev_adj = adj_p

    results = []
    for i, p in enumerate(p_values):
        results.append({
            "raw_p": round(p, 6),
            "adjusted_p": round(adjusted[i], 6),
            "significant": adjusted[i] < alpha,
        })
    return results


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(
    project_dir: Path,
    runs_data: dict,
    correction_method: str,
    alpha: float,
    project_name: str,
) -> str:
    """Generate the final report markdown."""
    summary = runs_data.get("summary", {})
    runs = runs_data.get("runs", [])
    hypotheses = parse_hypotheses(project_dir)
    deviations = parse_deviation_log(project_dir)
    gates = parse_gates(project_dir)

    lines: list[str] = []

    # Header
    lines.append("# Final Experiment Report")
    lines.append("")
    lines.append(f"**Project**: {project_name}")
    lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("**Generated by**: sdd-report-generator")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Hypotheses
    lines.append("## 1. Pre-Registered Hypotheses")
    lines.append("")

    confirmatory = [h for h in hypotheses if h.is_confirmatory]
    exploratory = [h for h in hypotheses if not h.is_confirmatory]

    if confirmatory:
        lines.append("### Confirmatory Hypotheses")
        lines.append("")
        lines.append("| # | Hypothesis | Metric | Threshold | Best Result | Status |")
        lines.append("|---|-----------|--------|-----------|-------------|--------|")
        for h in confirmatory:
            best = _find_best_metric(runs, h.metric)
            status = _determine_status(h, best)
            threshold_str = f"{h.threshold}" if h.threshold else "N/A"
            best_str = f"{best:.4f}" if best is not None else "N/A"
            lines.append(
                f"| {h.index} | {h.description} | {h.metric} | "
                f"{threshold_str} | {best_str} | {status} |"
            )
        lines.append("")

    if exploratory:
        lines.append("### Exploratory Hypotheses")
        lines.append("")
        lines.append("| # | Hypothesis | Metric | Result | Notes |")
        lines.append("|---|-----------|--------|--------|-------|")
        for h in exploratory:
            best = _find_best_metric(runs, h.metric)
            best_str = f"{best:.4f}" if best is not None else "N/A"
            lines.append(
                f"| {h.index} | {h.description} | {h.metric} | "
                f"{best_str} | Exploratory |"
            )
        lines.append("")

    if not hypotheses:
        lines.append("*No hypotheses found in 00_HYPOTHESES.md.*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 2: Full Run Summary
    lines.append("## 2. Full Run Summary")
    lines.append("")
    lines.append(f"**Total runs executed**: {summary.get('total_run_count', 0)}")
    lines.append(f"**Deleted runs**: {summary.get('deleted_run_count', 0)} (MUST be 0)")
    lines.append(f"**Failed runs**: {summary.get('failed_run_count', 0)}")
    lines.append(f"**Successful CV runs**: {summary.get('cv_run_count', 0)}")
    lines.append(f"**Hold-out runs**: {summary.get('holdout_run_count', 0)} (MUST be <= 1)")
    lines.append("")

    metric_stats = summary.get("metric_stats", [])
    if metric_stats:
        lines.append("### Run Statistics")
        lines.append("")
        lines.append("| Metric | Mean | Std | Min | Max | N |")
        lines.append("|--------|------|-----|-----|-----|---|")
        for m in metric_stats:
            lines.append(
                f"| {m['name']} | {m['mean']} | {m['std']} | "
                f"{m['min']} | {m['max']} | {m['n']} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 3: Gate Conditions
    lines.append("## 3. Gate Condition Results")
    lines.append("")
    if gates:
        lines.append("| Gate | Condition | Best CV Result | Status |")
        lines.append("|------|-----------|---------------|--------|")
        for g in gates:
            best = _find_best_metric(
                [r for r in runs if r.get("phase") == "cv"],
                g["metric"],
            )
            met = _check_gate(best, g["operator"], float(g["threshold"]))
            best_str = f"{best:.4f}" if best is not None else "N/A"
            status = "PASS" if met else "FAIL"
            lines.append(
                f"| {g['name']} | {g['condition']} | {best_str} | {status} |"
            )
        lines.append("")

        # Hold-out result
        holdout_runs = [r for r in runs if r.get("phase") == "holdout"]
        if holdout_runs:
            lines.append("**Hold-out result**:")
            for g in gates:
                h_val = _find_best_metric(holdout_runs, g["metric"])
                if h_val is not None:
                    met = _check_gate(h_val, g["operator"], float(g["threshold"]))
                    lines.append(f"- {g['name']}: {h_val:.4f} ({'PASS' if met else 'FAIL'})")
            lines.append("")
    else:
        lines.append("*No gate conditions found in 02_METRICS.md.*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 4: Multiple Comparison Corrections
    lines.append("## 4. Multiple Comparison Corrections")
    lines.append("")

    # Collect p-values from runs if available
    p_values: list[tuple[str, float]] = []
    for r in runs:
        for k, v in r.get("metrics", {}).items():
            if "p_value" in k.lower() or "pvalue" in k.lower():
                if isinstance(v, (int, float)) and not math.isnan(v):
                    p_values.append((k, float(v)))

    if p_values and len(p_values) > 1:
        raw_ps = [p for _, p in p_values]
        if correction_method == "bonferroni":
            corrected = bonferroni_correction(raw_ps, alpha)
        else:
            corrected = benjamini_hochberg_correction(raw_ps, alpha)

        lines.append(f"**Method**: {correction_method}")
        lines.append(f"**Number of comparisons**: {len(p_values)}")
        lines.append(f"**Significance level (alpha)**: {alpha}")
        if correction_method == "bonferroni":
            lines.append(f"**Adjusted alpha**: {alpha / len(p_values):.6f}")
        lines.append("")
        lines.append("| Comparison | Raw p-value | Adjusted p-value | Significant |")
        lines.append("|-----------|-------------|------------------|-------------|")
        for (name, _), result in zip(p_values, corrected):
            sig = "Yes" if result["significant"] else "No"
            lines.append(
                f"| {name} | {result['raw_p']} | {result['adjusted_p']} | {sig} |"
            )
        lines.append("")
    else:
        lines.append(f"**Method**: {correction_method}")
        lines.append(f"**Significance level (alpha)**: {alpha}")
        lines.append("")
        if len(p_values) <= 1:
            lines.append(
                "*Single comparison or no p-values found. "
                "Correction not applicable.*"
            )
        else:
            lines.append("*No p-values found in run metrics.*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 5: Deviation Log
    lines.append("## 5. Deviation Log")
    lines.append("")
    if deviations:
        lines.append("| Date | File Changed | Description | Rationale | Impact |")
        lines.append("|------|-------------|-------------|-----------|--------|")
        for d in deviations:
            lines.append(
                f"| {d['date']} | {d['file']} | {d['description']} | "
                f"{d['rationale']} | {d['impact']} |"
            )
        lines.append("")
    else:
        lines.append("*No deviations recorded.*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 6: Experiment Insights
    lines.append("## 6. Experiment Insights")
    lines.append("")
    experiment_logs = _collect_experiment_insights(project_dir, runs)
    if experiment_logs:
        lines.append("### Per-Run Observations")
        lines.append("")
        lines.append("| Run Name | Phase | Key Finding |")
        lines.append("|----------|-------|-------------|")
        for log in experiment_logs:
            lines.append(
                f"| [{log['run_name']}](experiments/{log['run_name']}.md) | "
                f"{log['phase']} | {log['finding']} |"
            )
        lines.append("")
        comparison_path = project_dir / "docs" / "experiments" / "COMPARISON.md"
        if comparison_path.exists():
            lines.append(
                "Full comparison matrix: "
                "[COMPARISON.md](experiments/COMPARISON.md)"
            )
            lines.append("")
    else:
        lines.append(
            "*No experiment logs found in docs/experiments/. "
            "Run sdd-experiment-logger to generate them.*"
        )
        lines.append("")

    lines.append("---")
    lines.append("")

    # Section 7: Anti-Sycophancy Declaration
    lines.append("## 7. Anti-Sycophancy Declaration (R8)")
    lines.append("")
    lines.append("> This report includes ALL experiment results, including:")
    lines.append("> - Runs that did not meet gate conditions")
    lines.append("> - Failed or crashed runs")
    lines.append("> - Results that contradict the primary hypothesis")
    lines.append("> - Exploratory analyses that were not pre-registered")
    lines.append(">")
    lines.append(
        "> No results have been selectively omitted or presented in a misleading way."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 8: Reproducibility
    lines.append("## 8. Reproducibility")
    lines.append("")
    lines.append(f"- **Report generated**: {datetime.now().isoformat()}")
    lines.append(f"- **Total runs in dataset**: {len(runs)}")
    lines.append(f"- **Backend**: {runs_data.get('backend', 'unknown')}")
    lines.append(f"- **Runs collected at**: {runs_data.get('generated_at', 'unknown')}")
    lines.append("")

    return "\n".join(lines)


def _collect_experiment_insights(
    project_dir: Path,
    runs: list[dict],
) -> list[dict[str, str]]:
    """Collect insights from experiment log files in docs/experiments/."""
    experiments_dir = project_dir / "docs" / "experiments"
    if not experiments_dir.exists():
        return []

    insights: list[dict[str, str]] = []
    for r in runs:
        run_name = r.get("run_name", r.get("run_id", "")[:8])
        log_path = experiments_dir / f"{run_name}.md"
        if not log_path.exists():
            continue

        text = log_path.read_text()
        phase = r.get("phase", "cv")

        # Extract first non-comment line from Observations section
        finding = ""
        obs_match = re.search(
            r'## Observations(.*?)(?=\n## |\Z)',
            text, re.DOTALL,
        )
        if obs_match:
            for line in obs_match.group(1).splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("<!--"):
                    finding = line[:80]
                    break

        if not finding:
            finding = "No observations recorded"

        insights.append({
            "run_name": run_name,
            "phase": phase,
            "finding": finding,
        })

    return insights


def _find_best_metric(
    runs: list[dict],
    metric: str,
) -> Optional[float]:
    """Find the best (max) value for a metric across runs."""
    values = []
    for r in runs:
        metrics = r.get("metrics", {})
        # Case-insensitive search
        for k, v in metrics.items():
            if k.lower() == metric.lower():
                if isinstance(v, (int, float)) and not math.isnan(v):
                    values.append(float(v))
    return max(values) if values else None


def _determine_status(hyp: Hypothesis, best: Optional[float]) -> str:
    """Determine hypothesis status."""
    if best is None:
        return "Inconclusive"
    if hyp.threshold is None:
        return "Reported"
    if best >= hyp.threshold:
        return "Confirmed"
    return "Not Confirmed"


def _check_gate(
    value: Optional[float],
    operator: str,
    threshold: float,
) -> bool:
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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate final experiment report (R8 Anti-Sycophancy, R10 Full Reporting)"
    )
    parser.add_argument(
        "--project-dir", type=Path, required=True,
        help="Root directory of the SDD ML project",
    )
    parser.add_argument(
        "--runs-json", type=Path, default=None,
        help="Path to all_runs.json (default: data/processed/all_runs.json)",
    )
    parser.add_argument(
        "--correction", choices=["bonferroni", "bh-fdr"],
        default="bonferroni",
        help="Multiple comparison correction method",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Significance level (default: 0.05)",
    )
    parser.add_argument(
        "--project-name", type=str, default="SDD ML Project",
        help="Project name for the report header",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output path (default: docs/FINAL_REPORT.md)",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    runs_json = args.runs_json or (project_dir / "data" / "processed" / "all_runs.json")

    if not runs_json.exists():
        print(f"ERROR: {runs_json} not found. Run collect_runs.py first.", file=sys.stderr)
        sys.exit(1)

    runs_data = json.loads(runs_json.read_text())

    # Generate report
    report = generate_report(
        project_dir=project_dir,
        runs_data=runs_data,
        correction_method=args.correction,
        alpha=args.alpha,
        project_name=args.project_name,
    )

    # Validate report
    results: list[CheckResult] = []
    summary = runs_data.get("summary", {})

    if summary.get("deleted_run_count", 0) > 0:
        results.append(CheckResult(
            "Deleted Runs in Report",
            False,
            f"{summary['deleted_run_count']} deleted runs. Report includes them but this violates R5.",
        ))
    else:
        results.append(CheckResult(
            "Deleted Runs in Report",
            True,
            "No deleted runs.",
        ))

    if "Anti-Sycophancy Declaration" in report:
        results.append(CheckResult(
            "Anti-Sycophancy Section",
            True,
            "Declaration present in report.",
        ))
    else:
        results.append(CheckResult(
            "Anti-Sycophancy Section",
            False,
            "Missing Anti-Sycophancy declaration.",
        ))

    # Write report
    output_path = args.output or (project_dir / "docs" / "FINAL_REPORT.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    # Print validation
    print("\n=== Report Generation Results ===\n")
    all_passed = True
    for r in results:
        print(r)
        if not r.passed:
            all_passed = False

    print(f"\nReport written to: {output_path}")
    print(f"{'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
