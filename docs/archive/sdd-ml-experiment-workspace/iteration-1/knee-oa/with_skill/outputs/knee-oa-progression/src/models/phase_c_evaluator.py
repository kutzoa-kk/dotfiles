"""Phase C evaluator: Holdout Evaluation (ONE-SHOT).

This module runs exactly once on the held-out temporal test set
(visit_date >= 2024-01-01).

Re-running after seeing results constitutes p-hacking.

Protocol:
    1. Load best model configuration from Phase B
    2. Train on full pre-2024 data
    3. Evaluate on post-2024 holdout data
    4. Report all metrics — no re-tuning allowed
"""

import logging
from dataclasses import dataclass, field

import numpy as np
from omegaconf import DictConfig
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.data_access import load_data
from src.features.feature_matrix_builder import build_feature_matrix
from src.models.trainer import train_model
from src.split_generator import generate_temporal_holdout

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseCResult:
    """Immutable result container for Phase C holdout evaluation."""

    metrics: dict[str, float]
    gates: dict[str, bool]
    holdout_run_count: int = 1  # Track how many times holdout was evaluated
    details: dict = field(default_factory=dict)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_c_evaluation(cfg: DictConfig) -> PhaseCResult:
    """Run one-shot holdout evaluation.

    WARNING: This function should be called AT MOST ONCE per experiment.
    """
    logger.warning(
        "Phase C: ONE-SHOT holdout evaluation. "
        "Do NOT re-run after seeing results."
    )

    # 1. Build feature matrix (full dataset)
    features_df, target_series, groups_series = build_feature_matrix(cfg)
    X = features_df.to_numpy()
    y = target_series.to_numpy().astype(float)

    # 2. Generate temporal holdout split
    df = load_data(cfg)
    train_idx, test_idx = generate_temporal_holdout(df, cfg)

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    logger.info(
        f"Holdout split: {len(train_idx)} train (< 2024), "
        f"{len(test_idx)} test (>= 2024)"
    )

    # 3. Train on full training data and predict holdout
    model, preds = train_model(cfg, X_train, y_train, X_test)

    # 4. Compute metrics
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))

    # Ordinal accuracy
    preds_rounded = np.clip(np.round(preds), 0, 4)
    ordinal_acc = float(np.mean(np.abs(y_test - preds_rounded) <= 1))
    exact_acc = float(np.mean(y_test == preds_rounded))

    metrics = {
        "holdout_rmse": rmse,
        "holdout_mae": mae,
        "holdout_ordinal_accuracy_within_1": ordinal_acc,
        "holdout_exact_accuracy": exact_acc,
        "holdout_n_train": float(len(train_idx)),
        "holdout_n_test": float(len(test_idx)),
    }

    # 5. Check gates (informational — holdout is always reported)
    gates = {
        "rmse": rmse <= cfg.gates.phase_c.max_rmse,
    }

    details = {
        "train_period": f"< {cfg.holdout.cutoff_date}",
        "test_period": f">= {cfg.holdout.cutoff_date}",
        "predictions_summary": {
            "mean": float(np.mean(preds)),
            "std": float(np.std(preds)),
            "min": float(np.min(preds)),
            "max": float(np.max(preds)),
        },
    }

    return PhaseCResult(
        metrics=metrics,
        gates=gates,
        details=details,
    )
