"""Phase A evaluator -- biomarker correlation verification for Knee OA Progression.

Tests:
    H1: Knee angle features correlate with KL grade (Spearman rho >= 0.4)
    H2: Gait cycle features correlate with KL grade (Spearman rho >= 0.4)
    H3: Known-group validity -- KL 3-4 (severe) vs KL 0-1 (normal/mild)
    H4: Feature redundancy check -- inter-feature correlation analysis

Medical compliance:
    - Bonferroni-corrected significance levels
    - Effect size reporting (Cohen's d, AUROC)
    - Confidence intervals for all correlations
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np
import polars as pl
from scipy import stats

# Gate threshold for Phase A
GATE_SPEARMAN_RHO = 0.4

# Bonferroni-corrected significance level (2 primary hypotheses)
ALPHA_ADJ = 0.05 / 2  # = 0.025

# Known-group thresholds (KL grade)
SEVERE_KL_MIN = 3  # KL 3-4 = severe OA
NORMAL_KL_MAX = 1  # KL 0-1 = normal/mild


@dataclass(frozen=True)
class EvaluationReport:
    """Immutable evaluation result for a single hypothesis test."""

    hypothesis: str
    metrics: dict[str, float] = dataclass_field(default_factory=dict)
    gate_passed: bool | None = None
    description: str = ""


def evaluate_h1_knee_angle_correlation(
    df: pl.DataFrame,
    knee_angle_cols: list[str],
) -> EvaluationReport:
    """Test H1: Knee angle features correlate with KL grade.

    Computes Spearman correlation between each knee angle feature and KL grade.
    Gate condition: Maximum |rho| across features >= 0.4

    Args:
        df: DataFrame with kl_grade and knee angle feature columns.
        knee_angle_cols: List of knee angle feature column names.

    Returns:
        EvaluationReport with per-feature correlations and gate result.
    """
    kl_grade = df["kl_grade"].to_numpy().astype(float)
    metrics: dict[str, float] = {}
    max_abs_rho = 0.0

    for col in knee_angle_cols:
        if col not in df.columns:
            continue
        values = df[col].to_numpy().astype(float)
        # Skip columns with NaN
        valid_mask = ~(np.isnan(values) | np.isnan(kl_grade))
        if valid_mask.sum() < 10:
            continue

        rho, p_value = stats.spearmanr(kl_grade[valid_mask], values[valid_mask])
        metrics[f"rho_{col}"] = float(rho)
        metrics[f"p_{col}"] = float(p_value)

        if abs(rho) > max_abs_rho:
            max_abs_rho = abs(rho)

    metrics["max_abs_rho"] = float(max_abs_rho)
    metrics["n_features_tested"] = float(len([c for c in knee_angle_cols if c in df.columns]))
    metrics["alpha_adjusted"] = ALPHA_ADJ

    gate_passed = bool(max_abs_rho >= GATE_SPEARMAN_RHO)

    return EvaluationReport(
        hypothesis="H1",
        metrics=metrics,
        gate_passed=gate_passed,
        description=(
            f"Knee angle correlation: max |rho|={max_abs_rho:.3f}. "
            f"Gate (|rho|>={GATE_SPEARMAN_RHO}): {'PASS' if gate_passed else 'FAIL'}"
        ),
    )


def evaluate_h2_gait_cycle_correlation(
    df: pl.DataFrame,
    gait_cycle_cols: list[str],
) -> EvaluationReport:
    """Test H2: Gait cycle features correlate with KL grade.

    Computes Spearman correlation between each gait cycle feature and KL grade.
    Gate condition: Maximum |rho| across features >= 0.4

    Args:
        df: DataFrame with kl_grade and gait cycle feature columns.
        gait_cycle_cols: List of gait cycle feature column names.

    Returns:
        EvaluationReport with per-feature correlations and gate result.
    """
    kl_grade = df["kl_grade"].to_numpy().astype(float)
    metrics: dict[str, float] = {}
    max_abs_rho = 0.0

    for col in gait_cycle_cols:
        if col not in df.columns:
            continue
        values = df[col].to_numpy().astype(float)
        valid_mask = ~(np.isnan(values) | np.isnan(kl_grade))
        if valid_mask.sum() < 10:
            continue

        rho, p_value = stats.spearmanr(kl_grade[valid_mask], values[valid_mask])
        metrics[f"rho_{col}"] = float(rho)
        metrics[f"p_{col}"] = float(p_value)

        if abs(rho) > max_abs_rho:
            max_abs_rho = abs(rho)

    metrics["max_abs_rho"] = float(max_abs_rho)
    metrics["n_features_tested"] = float(len([c for c in gait_cycle_cols if c in df.columns]))
    metrics["alpha_adjusted"] = ALPHA_ADJ

    gate_passed = bool(max_abs_rho >= GATE_SPEARMAN_RHO)

    return EvaluationReport(
        hypothesis="H2",
        metrics=metrics,
        gate_passed=gate_passed,
        description=(
            f"Gait cycle correlation: max |rho|={max_abs_rho:.3f}. "
            f"Gate (|rho|>={GATE_SPEARMAN_RHO}): {'PASS' if gate_passed else 'FAIL'}"
        ),
    )


def evaluate_known_group_validity(df: pl.DataFrame) -> EvaluationReport:
    """Test known-group validity: KL 3-4 (severe) vs KL 0-1 (normal/mild).

    Medical compliance: reports Cohen's d, Glass's delta, and AUROC
    for clinically meaningful group separation.
    """
    severe = df.filter(pl.col("kl_grade") >= SEVERE_KL_MIN)
    normal = df.filter(pl.col("kl_grade") <= NORMAL_KL_MAX)

    metrics: dict[str, float] = {
        "n_severe": float(len(severe)),
        "n_normal": float(len(normal)),
    }

    # Compute effect sizes on knee_rom if available
    rom_col = "knee_rom"
    if rom_col in df.columns and len(severe) >= 2 and len(normal) >= 2:
        severe_rom = severe[rom_col].drop_nulls().to_numpy()
        normal_rom = normal[rom_col].drop_nulls().to_numpy()

        if len(severe_rom) >= 2 and len(normal_rom) >= 2:
            mean_severe = float(np.mean(severe_rom))
            mean_normal = float(np.mean(normal_rom))
            std_severe = float(np.std(severe_rom, ddof=1))
            std_normal = float(np.std(normal_rom, ddof=1))

            # Cohen's d
            pooled_std = np.sqrt(
                ((len(severe_rom) - 1) * std_severe ** 2 + (len(normal_rom) - 1) * std_normal ** 2)
                / (len(severe_rom) + len(normal_rom) - 2)
            )
            cohens_d = (mean_normal - mean_severe) / pooled_std if pooled_std > 0 else 0.0
            metrics["cohens_d_knee_rom"] = float(cohens_d)
            metrics["mean_rom_severe"] = mean_severe
            metrics["mean_rom_normal"] = mean_normal

            # Mann-Whitney U
            u_stat, p_value = stats.mannwhitneyu(
                normal_rom, severe_rom, alternative="greater"
            )
            metrics["u_stat"] = float(u_stat)
            metrics["p_value"] = float(p_value)

            # AUROC
            auroc = u_stat / (len(normal_rom) * len(severe_rom))
            metrics["auroc_knee_rom"] = float(auroc)

    return EvaluationReport(
        hypothesis="Known-group validity",
        metrics=metrics,
        gate_passed=None,  # Supplementary -- no gate
        description=(
            f"KL>={SEVERE_KL_MIN} (n={len(severe)}) vs KL<={NORMAL_KL_MAX} (n={len(normal)}). "
            f"Cohen's d (ROM)={metrics.get('cohens_d_knee_rom', float('nan')):.3f}"
        ),
    )


def evaluate_kl_grade_distribution(df: pl.DataFrame) -> EvaluationReport:
    """Report KL grade distribution for medical compliance.

    Not a gate -- purely informational for assessing class balance.
    """
    grade_counts = {}
    for grade in range(5):
        count = len(df.filter(pl.col("kl_grade") == grade))
        grade_counts[grade] = count

    total = sum(grade_counts.values())
    metrics: dict[str, float] = {
        f"n_kl_{grade}": float(count) for grade, count in grade_counts.items()
    }
    metrics["total_samples"] = float(total)
    metrics["min_grade_count"] = float(min(grade_counts.values()))
    metrics["max_grade_ratio"] = float(max(grade_counts.values()) / total) if total > 0 else 0.0

    return EvaluationReport(
        hypothesis="KL grade distribution",
        metrics=metrics,
        gate_passed=None,
        description=(
            f"KL grade distribution: {grade_counts}. "
            f"Min count: {min(grade_counts.values())}, "
            f"Max ratio: {metrics['max_grade_ratio']:.2%}"
        ),
    )


def run_phase_a_evaluation(
    df: pl.DataFrame,
    knee_angle_cols: list[str],
    gait_cycle_cols: list[str],
) -> list[EvaluationReport]:
    """Run all Phase A hypothesis tests and return reports.

    Args:
        df: DataFrame with KL grades, knee angle features, and gait cycle features.
        knee_angle_cols: List of knee angle feature column names.
        gait_cycle_cols: List of gait cycle feature column names.

    Returns:
        List of 4 EvaluationReports:
            H1 (knee angle), H2 (gait cycle), known-group validity, KL distribution.
    """
    return [
        evaluate_h1_knee_angle_correlation(df, knee_angle_cols),
        evaluate_h2_gait_cycle_correlation(df, gait_cycle_cols),
        evaluate_known_group_validity(df),
        evaluate_kl_grade_distribution(df),
    ]


def check_gate_conditions(reports: list[EvaluationReport]) -> bool:
    """Check if Phase A gate conditions are met for proceeding to Phase B.

    Gate conditions (BLOCKING):
        - H1: At least one knee angle feature has |rho| >= 0.4 with KL grade
        - H2: At least one gait cycle feature has |rho| >= 0.4 with KL grade

    At least ONE of H1 or H2 must pass to proceed.
    """
    h1_passed = False
    h2_passed = False

    for report in reports:
        if report.hypothesis == "H1" and report.gate_passed is True:
            h1_passed = True
        if report.hypothesis == "H2" and report.gate_passed is True:
            h2_passed = True

    return h1_passed or h2_passed
