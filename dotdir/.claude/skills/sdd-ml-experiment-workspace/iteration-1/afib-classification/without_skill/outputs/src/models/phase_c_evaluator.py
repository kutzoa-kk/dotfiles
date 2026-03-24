"""Phase C evaluator -- hold-out ONE-SHOT evaluation and gate check.

Gate conditions (02_METRICS.md):
    PR-AUC >= 0.65

ONE-SHOT constraint: evaluate once, report, do not iterate.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.models.holdout_trainer import HoldoutResult

GATE_PR_AUC_PHASE_C = 0.65


@dataclass(frozen=True)
class HoldoutEvaluation:
    """Immutable hold-out evaluation result."""

    model_name: str
    pr_auc: float
    roc_auc: float
    f1: float
    precision: float
    recall: float
    brier_score: float
    baseline_pr_auc: float  # prevalence-only baseline
    pr_auc_improvement: float  # pr_auc - baseline
    n_samples: int
    n_positive: int
    n_subjects: int
    gate_passed: bool
    optimal_threshold: float
    description: str


def evaluate_holdout(
    holdout_result: HoldoutResult,
    optimal_threshold: float | None = None,
    gate_pr_auc: float = GATE_PR_AUC_PHASE_C,
) -> HoldoutEvaluation:
    """Evaluate hold-out predictions with gate check.

    Gate: PR-AUC >= gate_pr_auc

    Baseline: PR-AUC of a random predictor = prevalence.

    Args:
        holdout_result: Output from train_holdout_model.
        optimal_threshold: Threshold from CV. If None, optimized on holdout.
        gate_pr_auc: Minimum PR-AUC threshold.

    Returns:
        HoldoutEvaluation with gate determination.
    """
    preds = holdout_result.holdout_predictions
    y_true = preds["af_label_true"].to_numpy()
    y_prob = preds["af_prob_pred"].to_numpy()

    pr_auc = float(average_precision_score(y_true, y_prob))
    roc_auc = float(roc_auc_score(y_true, y_prob))

    # Baseline: prevalence (PR-AUC of random = prevalence)
    prevalence = float(y_true.sum() / len(y_true))
    baseline_pr_auc = prevalence
    pr_auc_improvement = pr_auc - baseline_pr_auc

    # Determine threshold
    if optimal_threshold is None:
        thresholds = np.linspace(0.01, 0.99, 99)
        best_f1 = 0.0
        best_threshold = 0.5
        for t in thresholds:
            y_pred_binary = (y_prob >= t).astype(int)
            if y_pred_binary.sum() == 0:
                continue
            current_f1 = float(f1_score(y_true, y_pred_binary, zero_division=0))
            if current_f1 > best_f1:
                best_f1 = current_f1
                best_threshold = t
        optimal_threshold = best_threshold

    y_pred_binary = (y_prob >= optimal_threshold).astype(int)

    f1_val = float(f1_score(y_true, y_pred_binary, zero_division=0))
    prec = float(precision_score(y_true, y_pred_binary, zero_division=0))
    rec = float(recall_score(y_true, y_pred_binary, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))

    n_positive = int(y_true.sum())
    n_subjects = len(preds["record_id"].unique())

    gate_passed = bool(pr_auc >= gate_pr_auc)

    return HoldoutEvaluation(
        model_name=holdout_result.model_name,
        pr_auc=pr_auc,
        roc_auc=roc_auc,
        f1=f1_val,
        precision=prec,
        recall=rec,
        brier_score=brier,
        baseline_pr_auc=baseline_pr_auc,
        pr_auc_improvement=pr_auc_improvement,
        n_samples=len(y_true),
        n_positive=n_positive,
        n_subjects=n_subjects,
        gate_passed=gate_passed,
        optimal_threshold=optimal_threshold,
        description=(
            f"Hold-out ONE-SHOT [{holdout_result.model_name}]: "
            f"PR-AUC={pr_auc:.3f} (baseline={baseline_pr_auc:.3f}, "
            f"improvement={pr_auc_improvement:.3f}), "
            f"ROC-AUC={roc_auc:.3f}, F1={f1_val:.3f}, "
            f"Brier={brier:.3f}. "
            f"Gate (PR-AUC>={gate_pr_auc}): "
            f"{'PASS' if gate_passed else 'FAIL'}"
        ),
    )
