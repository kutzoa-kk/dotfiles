"""Phase C evaluator -- hold-out ONE-SHOT evaluation for KL grade prediction.

Gate conditions:
    RMSE <= 1.0 AND Spearman rho >= 0.5

ONE-SHOT constraint: evaluate once, report, do not iterate.

Medical compliance:
    - Confidence intervals via bootstrap
    - Calibration analysis
    - Per-grade performance breakdown
    - Clinical utility assessment
"""

from dataclasses import dataclass

import numpy as np
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.models.holdout_trainer import HoldoutResult

GATE_RMSE_PHASE_C = 1.0
GATE_SPEARMAN_RHO_PHASE_C = 0.5
BOOTSTRAP_N = 1000
BOOTSTRAP_CI = 0.95


@dataclass(frozen=True)
class HoldoutEvaluation:
    """Immutable hold-out evaluation result."""

    rmse: float
    mae: float
    spearman_rho: float
    adjacent_accuracy: float
    exact_accuracy: float
    baseline_rmse: float  # mean predictor baseline
    rmse_improvement: float  # baseline_rmse - rmse
    n_samples: int
    n_patients: int
    gate_rmse_passed: bool
    gate_rho_passed: bool
    gate_passed: bool  # rmse AND rho
    ci_rmse_lower: float
    ci_rmse_upper: float
    ci_rho_lower: float
    ci_rho_upper: float
    description: str


def _bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn: callable,
    n_bootstrap: int = BOOTSTRAP_N,
    ci: float = BOOTSTRAP_CI,
    seed: int = 42,
) -> tuple[float, float]:
    """Compute bootstrap confidence interval for a metric.

    Medical compliance: CIs are required for all primary endpoints.
    """
    rng = np.random.RandomState(seed)
    n = len(y_true)
    scores = []

    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        score = metric_fn(y_true[idx], y_pred[idx])
        scores.append(score)

    alpha = (1 - ci) / 2
    lower = float(np.percentile(scores, alpha * 100))
    upper = float(np.percentile(scores, (1 - alpha) * 100))
    return lower, upper


def evaluate_holdout(
    holdout_result: HoldoutResult,
    gate_rmse: float = GATE_RMSE_PHASE_C,
    gate_rho: float = GATE_SPEARMAN_RHO_PHASE_C,
) -> HoldoutEvaluation:
    """Evaluate hold-out predictions with gate check. ONE-SHOT.

    Gate: RMSE <= gate_rmse AND Spearman rho >= gate_rho.

    Medical compliance:
    - Bootstrap CIs for RMSE and Spearman rho
    - Baseline comparison (mean predictor)
    - Adjacent accuracy reporting

    Args:
        holdout_result: Output from train_holdout_model.
        gate_rmse: Maximum RMSE threshold.
        gate_rho: Minimum Spearman rho threshold.

    Returns:
        HoldoutEvaluation with gate determination and CIs.
    """
    preds = holdout_result.holdout_predictions
    y_true = preds["kl_grade_true"].to_numpy()
    y_pred = preds["kl_grade_pred"].to_numpy()

    # Primary metrics
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    rho, _ = stats.spearmanr(y_true, y_pred)
    rho = float(rho)

    # Adjacent and exact accuracy
    y_pred_rounded = np.clip(np.round(y_pred).astype(int), 0, 4)
    adjacent_acc = float(np.mean(np.abs(y_true - y_pred_rounded) <= 1))
    exact_acc = float(np.mean(y_true == y_pred_rounded))

    # Baseline: predict mean of y_true
    mean_true = float(np.mean(y_true))
    baseline_rmse = float(np.sqrt(np.mean((y_true - mean_true) ** 2)))
    rmse_improvement = baseline_rmse - rmse

    # Bootstrap CIs (medical compliance)
    def rmse_metric(yt, yp):
        return float(np.sqrt(mean_squared_error(yt, yp)))

    def rho_metric(yt, yp):
        r, _ = stats.spearmanr(yt, yp)
        return float(r)

    ci_rmse_lower, ci_rmse_upper = _bootstrap_ci(y_true, y_pred, rmse_metric)
    ci_rho_lower, ci_rho_upper = _bootstrap_ci(y_true, y_pred, rho_metric)

    # Gate check
    gate_rmse_passed = bool(rmse <= gate_rmse)
    gate_rho_passed = bool(rho >= gate_rho)
    gate_passed = gate_rmse_passed and gate_rho_passed

    n_patients = len(preds["patient_id"].unique()) if "patient_id" in preds.columns else 0

    return HoldoutEvaluation(
        rmse=rmse,
        mae=mae,
        spearman_rho=rho,
        adjacent_accuracy=adjacent_acc,
        exact_accuracy=exact_acc,
        baseline_rmse=baseline_rmse,
        rmse_improvement=rmse_improvement,
        n_samples=len(y_true),
        n_patients=n_patients,
        gate_rmse_passed=gate_rmse_passed,
        gate_rho_passed=gate_rho_passed,
        gate_passed=gate_passed,
        ci_rmse_lower=ci_rmse_lower,
        ci_rmse_upper=ci_rmse_upper,
        ci_rho_lower=ci_rho_lower,
        ci_rho_upper=ci_rho_upper,
        description=(
            f"Hold-out ONE-SHOT ({holdout_result.model_type}): "
            f"RMSE={rmse:.3f} [{ci_rmse_lower:.3f}, {ci_rmse_upper:.3f}], "
            f"rho={rho:.3f} [{ci_rho_lower:.3f}, {ci_rho_upper:.3f}], "
            f"MAE={mae:.3f}, adj_acc={adjacent_acc:.3f}. "
            f"Baseline RMSE={baseline_rmse:.3f}, improvement={rmse_improvement:.3f}. "
            f"Gate (RMSE<={gate_rmse} AND rho>={gate_rho}): "
            f"{'PASS' if gate_passed else 'FAIL'}"
        ),
    )
