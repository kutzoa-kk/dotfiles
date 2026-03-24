"""Phase A evaluator: Biomarker Correlation Validation.

Validates that KL grade correlates with known biomechanical biomarkers
before building prediction models.

Validations:
- Spearman correlation between KL grade and knee angle features
- Spearman correlation between KL grade and gait cycle features
- Batch effect check between left/right sides
- Distribution check of KL grade (no extreme class imbalance)
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import polars as pl
from omegaconf import DictConfig
from scipy import stats

from src.data_access import load_data

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseAResult:
    """Immutable result container for Phase A evaluation."""

    metrics: dict[str, float]
    gates: dict[str, bool]
    details: dict = field(default_factory=dict)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_a_evaluation(cfg: DictConfig) -> PhaseAResult:
    """Run Phase A validation checks.

    Checks:
    1. Spearman correlation of KL grade with knee angle biomarkers
    2. Spearman correlation of KL grade with gait cycle biomarkers
    3. Left/right side batch effect test
    4. KL grade distribution adequacy

    Args:
        cfg: Hydra config with data paths, thresholds, etc.

    Returns:
        PhaseAResult with metrics and gate pass/fail status.
    """
    # 1. Load data
    df = load_data(cfg)
    target_col = cfg.data.target_column
    min_rho = cfg.gates.phase_a.min_spearman_rho

    logger.info(f"Loaded {len(df)} samples for Phase A evaluation")

    metrics: dict[str, float] = {}
    gates: dict[str, bool] = {}
    details: dict[str, object] = {}

    target = df.get_column(target_col).to_numpy()

    # 2. Correlations with knee angle features
    knee_angle_cols = [
        c for c in df.columns
        if any(
            kw in c.lower()
            for kw in ["flexion", "extension", "varus", "valgus", "rotation"]
        )
        and c != target_col
    ]

    best_knee_rho = 0.0
    knee_correlations = {}
    for col in knee_angle_cols:
        values = df.get_column(col).to_numpy()
        valid_mask = ~(np.isnan(values) | np.isnan(target))
        if valid_mask.sum() < 10:
            continue
        rho, p_val = stats.spearmanr(target[valid_mask], values[valid_mask])
        knee_correlations[col] = {"rho": rho, "p_value": p_val}
        if abs(rho) > abs(best_knee_rho):
            best_knee_rho = rho

    metrics["best_knee_angle_rho"] = abs(best_knee_rho)
    gates["knee_angle_correlation"] = abs(best_knee_rho) >= min_rho
    details["knee_angle_correlations"] = knee_correlations

    # 3. Correlations with gait cycle features
    gait_cols = [
        c for c in df.columns
        if any(
            kw in c.lower()
            for kw in ["stance", "swing", "stride", "cadence", "gait", "double_support"]
        )
        and c != target_col
    ]

    best_gait_rho = 0.0
    gait_correlations = {}
    for col in gait_cols:
        values = df.get_column(col).to_numpy()
        valid_mask = ~(np.isnan(values) | np.isnan(target))
        if valid_mask.sum() < 10:
            continue
        rho, p_val = stats.spearmanr(target[valid_mask], values[valid_mask])
        gait_correlations[col] = {"rho": rho, "p_value": p_val}
        if abs(rho) > abs(best_gait_rho):
            best_gait_rho = rho

    metrics["best_gait_cycle_rho"] = abs(best_gait_rho)
    gates["gait_cycle_correlation"] = abs(best_gait_rho) >= min_rho
    details["gait_cycle_correlations"] = gait_correlations

    # 4. Overall best correlation (primary gate)
    overall_best_rho = max(abs(best_knee_rho), abs(best_gait_rho))
    metrics["overall_best_rho"] = overall_best_rho
    gates["overall_biomarker_correlation"] = overall_best_rho >= min_rho

    # 5. Batch effect check: L/R side
    if cfg.data.side_column in df.columns:
        side_col = cfg.data.side_column
        left_targets = df.filter(pl.col(side_col) == "L").get_column(target_col).to_numpy()
        right_targets = df.filter(pl.col(side_col) == "R").get_column(target_col).to_numpy()

        if len(left_targets) > 0 and len(right_targets) > 0:
            stat_val, p_value = stats.mannwhitneyu(
                left_targets, right_targets, alternative="two-sided"
            )
            metrics["side_batch_effect_p"] = p_value
            # No significant difference is expected (p > 0.05 means no batch effect)
            gates["no_side_batch_effect"] = p_value > 0.05
            details["side_batch_effect"] = {
                "statistic": stat_val,
                "p_value": p_value,
                "n_left": len(left_targets),
                "n_right": len(right_targets),
            }

    # 6. KL grade distribution
    unique_grades = np.unique(target[~np.isnan(target)])
    grade_counts = {
        int(g): int(np.sum(target == g)) for g in unique_grades
    }
    metrics["n_kl_grades"] = float(len(unique_grades))
    metrics["min_grade_count"] = float(min(grade_counts.values())) if grade_counts else 0.0
    details["kl_grade_distribution"] = grade_counts

    return PhaseAResult(metrics=metrics, gates=gates, details=details)
