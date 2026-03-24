"""Phase B evaluator: Regression Model Cross-Validation.

Trains ordinal regression models (LightGBM, XGBoost) with GroupKFold CV
to predict KL grade (0-4) from knee angle and gait cycle features.

Gate condition: RMSE <= 1.0 on cross-validated OOF predictions.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import polars as pl
from omegaconf import DictConfig
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.features.feature_matrix_builder import build_feature_matrix
from src.models.trainer import train_model
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
    """Compute regression metrics for KL grade prediction.

    Args:
        y_true: True KL grades.
        y_pred: Predicted KL grades (continuous).

    Returns:
        Dictionary of metric names to values.
    """
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))

    # Ordinal accuracy: predicted grade within 1 of true grade
    y_pred_rounded = np.clip(np.round(y_pred), 0, 4)
    ordinal_accuracy = float(np.mean(np.abs(y_true - y_pred_rounded) <= 1))

    # Exact match accuracy
    exact_accuracy = float(np.mean(y_true == y_pred_rounded))

    return {
        "rmse": rmse,
        "mae": mae,
        "ordinal_accuracy_within_1": ordinal_accuracy,
        "exact_accuracy": exact_accuracy,
    }


def aggregate_fold_metrics(
    fold_results: list[FoldResult],
) -> dict[str, float]:
    """Aggregate metrics across folds (mean and std)."""
    all_metric_names = fold_results[0].metrics.keys()
    aggregated = {}

    for metric_name in all_metric_names:
        values = [fr.metrics[metric_name] for fr in fold_results]
        aggregated[f"{metric_name}_mean"] = float(np.mean(values))
        aggregated[f"{metric_name}_std"] = float(np.std(values))

    return aggregated


def run_phase_b_evaluation(cfg: DictConfig) -> PhaseBResult:
    """Run Phase B cross-validated prediction.

    Args:
        cfg: Hydra config with model params, split config, gate thresholds.

    Returns:
        PhaseBResult with per-fold and aggregate metrics.
    """
    # 1. Build feature matrix
    features_df, target_series, groups_series = build_feature_matrix(cfg)
    X = features_df.to_numpy()
    y = target_series.to_numpy().astype(float)
    groups = groups_series.to_numpy()
    feature_names = features_df.columns

    logger.info(f"Feature matrix: {X.shape[0]} samples, {X.shape[1]} features")

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

        # Extract feature importance if available
        feat_importance = None
        if hasattr(model, "feature_importances_"):
            feat_importance = dict(zip(feature_names, model.feature_importances_))

        fold_results.append(
            FoldResult(
                fold_idx=fold_idx,
                metrics=fold_metrics,
                oof_predictions=preds,
                feature_importance=feat_importance,
            )
        )

    # 4. Aggregate metrics
    aggregate = aggregate_fold_metrics(fold_results)

    # Also compute OOF metrics on full dataset
    valid_mask = ~np.isnan(oof_preds)
    oof_metrics = compute_metrics(y[valid_mask], oof_preds[valid_mask])
    aggregate["oof_rmse"] = oof_metrics["rmse"]
    aggregate["oof_mae"] = oof_metrics["mae"]
    aggregate["oof_ordinal_accuracy_within_1"] = oof_metrics["ordinal_accuracy_within_1"]

    # 5. Check gates
    gates = {
        "rmse": aggregate["rmse_mean"] <= cfg.gates.phase_b.max_rmse,
    }

    return PhaseBResult(
        fold_results=fold_results,
        aggregate_metrics=aggregate,
        gates=gates,
        oof_predictions=oof_preds,
    )
