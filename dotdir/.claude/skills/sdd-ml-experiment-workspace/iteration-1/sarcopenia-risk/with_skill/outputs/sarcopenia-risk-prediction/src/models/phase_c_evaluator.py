"""Phase C evaluator: Holdout evaluation (ONE-SHOT).

This module runs exactly once on the held-out test set.
Re-running after seeing results constitutes p-hacking.

Protocol:
1. Train final model on full training set (80% of subjects)
2. Evaluate on holdout set (20% of subjects)
3. Report all metrics — do NOT iterate
"""

import logging
from dataclasses import dataclass, field

import numpy as np
from omegaconf import DictConfig
from scipy import stats

from src.features.feature_matrix_builder import build_feature_matrix
from src.models.lgb_trainer import train_model
from src.split_generator import generate_holdout_split

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseCResult:
    """Immutable result container for Phase C evaluation."""

    metrics: dict[str, float]
    gates: dict[str, bool]
    holdout_run_count: int = 1

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_c_evaluation(cfg: DictConfig) -> PhaseCResult:
    """Run one-shot holdout evaluation.

    WARNING: This function should be called AT MOST ONCE per experiment.

    Args:
        cfg: Hydra config with model params and holdout config.

    Returns:
        PhaseCResult with holdout metrics.
    """
    logger.warning(
        "Phase C: ONE-SHOT holdout evaluation. "
        "Do NOT re-tune and re-evaluate."
    )

    # 1. Build full feature matrix
    X, y, groups = build_feature_matrix(cfg)

    # 2. Generate holdout split
    train_idx, test_idx = generate_holdout_split(
        groups,
        test_ratio=cfg.holdout.test_ratio,
        random_state=cfg.holdout.random_state,
    )
    logger.info(
        f"Holdout split: train={len(train_idx)}, test={len(test_idx)}"
    )

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # 3. Train on full training set and predict holdout
    model, preds = train_model(cfg, X_train, y_train, X_test)

    # 4. Compute metrics
    rho, p_value = stats.spearmanr(y_test, preds)
    rmse = float(np.sqrt(np.mean((y_test - preds) ** 2)))
    mae = float(np.mean(np.abs(y_test - preds)))

    metrics = {
        "spearman_rho": float(rho),
        "spearman_p_value": float(p_value),
        "rmse": rmse,
        "mae": mae,
        "n_train": float(len(train_idx)),
        "n_test": float(len(test_idx)),
    }

    # 5. Gates (report only for Phase C — no strict rejection)
    gates = {
        "spearman_rho": float(rho) >= cfg.gates.phase_c.min_spearman_rho,
    }

    logger.info(f"Phase C holdout metrics: {metrics}")
    logger.info(f"Phase C gates: {gates}")

    return PhaseCResult(metrics=metrics, gates=gates)
