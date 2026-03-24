"""Phase C evaluator: Holdout evaluation (ONE-SHOT).

This module runs exactly once on the held-out test set.
Re-running after seeing results constitutes p-hacking.

Gate condition: PR-AUC >= 0.65 on holdout.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
from omegaconf import DictConfig

from src.features.feature_matrix_builder import build_feature_matrix
from src.models.classification_trainer import train_model
from src.models.metrics import compute_classification_metrics
from src.split_generator import generate_holdout_split

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseCResult:
    """Immutable result container for Phase C holdout evaluation."""

    metrics: dict[str, float]
    gates: dict[str, bool]
    holdout_run_count: int = 1
    details: dict = field(default_factory=dict)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_c_evaluation(cfg: DictConfig) -> PhaseCResult:
    """Run one-shot holdout evaluation for AF classification.

    WARNING: This function should be called AT MOST ONCE per experiment.
    Re-running after seeing results invalidates the holdout guarantee.

    Args:
        cfg: Hydra config with model params, holdout config, gate thresholds.

    Returns:
        PhaseCResult with holdout metrics and gate pass/fail status.
    """
    # 1. Build feature matrix
    x, y, groups = build_feature_matrix(cfg)

    # 2. Generate holdout split
    train_idx, test_idx = generate_holdout_split(cfg, groups)

    x_train, x_test = x[train_idx], x[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    logger.info(
        f"Holdout split: train={len(train_idx)}, test={len(test_idx)}"
    )
    logger.info(
        f"Train positive rate: {np.mean(y_train):.3f}, "
        f"Test positive rate: {np.mean(y_test):.3f}"
    )

    # 3. Train on full training set and predict on holdout
    model, probas = train_model(cfg, x_train, y_train, x_test)

    # 4. Compute metrics
    metrics = compute_classification_metrics(y_test, probas)

    # 5. Check gates
    gates = {
        "pr_auc": metrics["pr_auc"] >= cfg.gates.phase_c.pr_auc,
    }

    logger.info(f"Holdout PR-AUC: {metrics['pr_auc']:.4f}")
    logger.info(f"Holdout ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Holdout F1: {metrics['f1']:.4f}")

    return PhaseCResult(
        metrics=metrics,
        gates=gates,
        details={
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "train_positive_rate": float(np.mean(y_train)),
            "test_positive_rate": float(np.mean(y_test)),
        },
    )
