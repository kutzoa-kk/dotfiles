"""Phase B evaluator -- OOF prediction evaluation and gate check.

Evaluates out-of-fold (OOF) AF classification predictions.
Gate: pooled PR-AUC >= 0.70
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

from src.models.cv_trainer import CVTrainingResult

GATE_PR_AUC_PHASE_B = 0.70


@dataclass(frozen=True)
class PhaseBEvaluation:
    """Immutable Phase B evaluation result."""

    model_name: str
    pr_auc: float
    roc_auc: float
    f1: float
    precision: float
    recall: float
    brier_score: float
    n_samples: int
    n_positive: int
    gate_passed: bool
    metrics: dict[str, float]
    description: str


def evaluate_phase_b(
    training_result: CVTrainingResult,
    gate_pr_auc: float = GATE_PR_AUC_PHASE_B,
) -> PhaseBEvaluation:
    """Evaluate Phase B OOF predictions.

    Gate: pooled PR-AUC >= gate_pr_auc

    Args:
        training_result: Output from train_cv_model.
        gate_pr_auc: Minimum PR-AUC threshold.

    Returns:
        PhaseBEvaluation with gate determination.
    """
    oof = training_result.oof_predictions
    y_true = oof["af_label_true"].to_numpy()
    y_prob = oof["af_prob_pred"].to_numpy()

    # Primary metric
    pr_auc = training_result.pooled_pr_auc
    roc_auc = training_result.pooled_roc_auc

    # Optimal threshold from PR curve (maximize F1)
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

    y_pred_binary = (y_prob >= best_threshold).astype(int)

    f1_val = float(f1_score(y_true, y_pred_binary, zero_division=0))
    prec = float(precision_score(y_true, y_pred_binary, zero_division=0))
    rec = float(recall_score(y_true, y_pred_binary, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))
    n_positive = int(y_true.sum())

    metrics: dict[str, float] = {
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "f1": f1_val,
        "precision": prec,
        "recall": rec,
        "brier_score": brier,
        "optimal_threshold": best_threshold,
        "n_samples": float(len(y_true)),
        "n_positive": float(n_positive),
        "prevalence": float(n_positive / len(y_true)),
    }

    # Per-fold metrics
    for fr in training_result.fold_results:
        metrics[f"fold_{fr.fold}_pr_auc"] = fr.pr_auc
        metrics[f"fold_{fr.fold}_roc_auc"] = fr.roc_auc

    gate_passed = bool(pr_auc >= gate_pr_auc)

    return PhaseBEvaluation(
        model_name=training_result.model_name,
        pr_auc=pr_auc,
        roc_auc=roc_auc,
        f1=f1_val,
        precision=prec,
        recall=rec,
        brier_score=brier,
        n_samples=len(y_true),
        n_positive=n_positive,
        gate_passed=gate_passed,
        metrics=metrics,
        description=(
            f"Phase B [{training_result.model_name}]: "
            f"PR-AUC={pr_auc:.3f}, ROC-AUC={roc_auc:.3f}, "
            f"F1={f1_val:.3f} (threshold={best_threshold:.2f}), "
            f"Brier={brier:.3f}. "
            f"Gate (PR-AUC>={gate_pr_auc}): "
            f"{'PASS' if gate_passed else 'FAIL'}"
        ),
    )
