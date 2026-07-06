"""Phase B evaluator: Prediction Model CV.

Trains LightGBM with GroupKFold 5-fold CV and evaluates
sarcopenia risk prediction performance.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
from omegaconf import DictConfig
from scipy import stats

from src.features.feature_matrix_builder import build_feature_matrix
from src.models.lgb_trainer import train_model
from src.split_generator import generate_splits

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FoldResult:
    """Result from a single CV fold."""

    fold_idx: int
    metrics: dict[str, float]
    oof_predictions: np.ndarray
    feature_importance: dict[str, float] | None = None


@dataclass(frozen=True)
class PhaseBResult:
    """Immutable result container for Phase B evaluation."""

    fold_results: list[FoldResult]
    aggregate_metrics: dict[str, float]
    gates: dict[str, bool]
    oof_predictions: np.ndarray | None = None

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute regression evaluation metrics.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Dictionary of metric name -> value.
    """
    rho, p_value = stats.spearmanr(y_true, y_pred)
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mae = float(np.mean(np.abs(y_true - y_pred)))

    return {
        "spearman_rho": float(rho),
        "spearman_p_value": float(p_value),
        "rmse": rmse,
        "mae": mae,
    }


def aggregate_fold_metrics(
    fold_results: list[FoldResult],
) -> dict[str, float]:
    """Aggregate metrics across CV folds.

    Args:
        fold_results: List of per-fold results.

    Returns:
        Dictionary with mean and std of each metric.
    """
    metric_names = fold_results[0].metrics.keys()
    aggregate = {}

    for name in metric_names:
        values = [fr.metrics[name] for fr in fold_results]
        aggregate[f"{name}_mean"] = float(np.mean(values))
        aggregate[f"{name}_std"] = float(np.std(values))

    return aggregate


def run_phase_b_evaluation(cfg: DictConfig) -> PhaseBResult:
    """Run Phase B cross-validated prediction.

    Args:
        cfg: Hydra config with model params, split config, gate thresholds.

    Returns:
        PhaseBResult with per-fold and aggregate metrics.
    """
    # 1. Build feature matrix
    X, y, groups = build_feature_matrix(cfg)
    logger.info(f"Phase B: {X.shape[0]} samples, {X.shape[1]} features")

    # 2. Generate CV splits
    splits = generate_splits(cfg, groups)

    # 3. Train and evaluate per fold
    fold_results = []
    oof_preds = np.full(len(y), np.nan)

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        logger.info(f"Fold {fold_idx}: train={len(train_idx)}, val={len(val_idx)}")

        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model, preds = train_model(cfg, X_train, y_train, X_val)
        oof_preds[val_idx] = preds

        fold_metrics = compute_metrics(y_val, preds)
        logger.info(f"  Fold {fold_idx} metrics: {fold_metrics}")

        fold_results.append(
            FoldResult(
                fold_idx=fold_idx,
                metrics=fold_metrics,
                oof_predictions=preds,
            )
        )

    # 4. Aggregate metrics
    aggregate = aggregate_fold_metrics(fold_results)

    # 5. OOF-level metrics (using all OOF predictions)
    oof_metrics = compute_metrics(y, oof_preds)
    aggregate["oof_spearman_rho"] = oof_metrics["spearman_rho"]
    aggregate["oof_rmse"] = oof_metrics["rmse"]

    # 6. Check gates
    gates = {
        "spearman_rho": aggregate["oof_spearman_rho"]
        >= cfg.gates.phase_b.min_spearman_rho,
    }

    logger.info(f"Phase B aggregate: {aggregate}")
    logger.info(f"Phase B gates: {gates}")

    return PhaseBResult(
        fold_results=fold_results,
        aggregate_metrics=aggregate,
        gates=gates,
        oof_predictions=oof_preds,
    )
