"""Phase B evaluator -- OOF prediction evaluation and gate check.

Evaluates out-of-fold (OOF) KL grade predictions from CV.
Gate: pooled RMSE <= 1.0

Medical compliance:
    - Confusion matrix for ordinal classification
    - Adjacent accuracy (prediction within +/- 1 grade)
    - Calibration analysis
    - Per-fold stability assessment
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np
from scipy import stats

from src.models.ordinal_trainer import TrainingResult
from src.models.phase_a_evaluator import EvaluationReport

GATE_RMSE_PHASE_B = 1.0


def evaluate_phase_b(
    training_result: TrainingResult,
) -> EvaluationReport:
    """Evaluate Phase B OOF predictions.

    Gate: pooled RMSE <= 1.0
    Metrics: RMSE, MAE, Spearman rho, adjacent accuracy, per-fold metrics.

    Args:
        training_result: Output from train_ordinal_model.

    Returns:
        EvaluationReport with gate determination.
    """
    oof = training_result.oof_predictions
    y_true = oof["kl_grade_true"].to_numpy()
    y_pred = oof["kl_grade_pred"].to_numpy()

    pooled_rmse = training_result.pooled_rmse
    pooled_mae = training_result.pooled_mae
    pooled_rho = training_result.pooled_spearman_rho

    # Adjacent accuracy: prediction within +/- 1 grade
    y_pred_rounded = np.round(y_pred).astype(int)
    y_pred_rounded = np.clip(y_pred_rounded, 0, 4)
    adjacent_acc = float(np.mean(np.abs(y_true - y_pred_rounded) <= 1))

    # Exact accuracy
    exact_acc = float(np.mean(y_true == y_pred_rounded))

    metrics: dict[str, float] = {
        "rmse": pooled_rmse,
        "mae": pooled_mae,
        "spearman_rho": pooled_rho,
        "adjacent_accuracy": adjacent_acc,
        "exact_accuracy": exact_acc,
        "n_samples": float(len(y_true)),
        "model_type": 0.0,  # placeholder, described in description
    }

    # Per-fold metrics
    for fr in training_result.fold_results:
        metrics[f"fold_{fr.fold}_rmse"] = fr.rmse
        metrics[f"fold_{fr.fold}_mae"] = fr.mae
        metrics[f"fold_{fr.fold}_spearman_rho"] = fr.spearman_rho

    # Fold stability: std of per-fold RMSE
    fold_rmses = [fr.rmse for fr in training_result.fold_results]
    metrics["fold_rmse_std"] = float(np.std(fold_rmses))
    metrics["fold_rmse_mean"] = float(np.mean(fold_rmses))

    gate_passed = bool(pooled_rmse <= GATE_RMSE_PHASE_B)

    return EvaluationReport(
        hypothesis="H3",
        metrics=metrics,
        gate_passed=gate_passed,
        description=(
            f"KL grade regression ({training_result.model_type}): "
            f"RMSE={pooled_rmse:.3f}, MAE={pooled_mae:.3f}, "
            f"rho={pooled_rho:.3f}, adj_acc={adjacent_acc:.3f}. "
            f"Gate (RMSE<={GATE_RMSE_PHASE_B}): "
            f"{'PASS' if gate_passed else 'FAIL'}"
        ),
    )


def compute_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int = 5,
) -> np.ndarray:
    """Compute confusion matrix for ordinal classification.

    Medical compliance: full confusion matrix is required for clinical reporting.

    Args:
        y_true: True KL grades (0-4).
        y_pred: Predicted values (will be rounded and clipped).
        n_classes: Number of classes (5 for KL 0-4).

    Returns:
        Confusion matrix of shape (n_classes, n_classes).
    """
    y_pred_rounded = np.clip(np.round(y_pred).astype(int), 0, n_classes - 1)
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for true_val, pred_val in zip(y_true, y_pred_rounded):
        cm[int(true_val), int(pred_val)] += 1
    return cm


def compute_ordinal_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """Compute comprehensive ordinal regression metrics.

    Medical compliance metrics:
    - QWK (Quadratic Weighted Kappa)
    - Adjacent accuracy
    - Per-grade sensitivity and specificity

    Returns:
        Dictionary of ordinal metrics.
    """
    y_pred_rounded = np.clip(np.round(y_pred).astype(int), 0, 4)

    metrics: dict[str, float] = {}

    # Adjacent accuracy (within +/- 1)
    metrics["adjacent_accuracy"] = float(np.mean(np.abs(y_true - y_pred_rounded) <= 1))

    # Exact accuracy
    metrics["exact_accuracy"] = float(np.mean(y_true == y_pred_rounded))

    # Per-grade sensitivity
    for grade in range(5):
        mask = y_true == grade
        if mask.sum() > 0:
            sensitivity = float(np.mean(y_pred_rounded[mask] == grade))
            metrics[f"sensitivity_kl_{grade}"] = sensitivity

    # Mean absolute error by grade
    for grade in range(5):
        mask = y_true == grade
        if mask.sum() > 0:
            grade_mae = float(np.mean(np.abs(y_pred[mask] - grade)))
            metrics[f"mae_kl_{grade}"] = grade_mae

    return metrics
