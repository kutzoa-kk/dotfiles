"""Phase B evaluator: Classification Model CV.

Trains LightGBM / Logistic Regression classifiers with
StratifiedGroupKFold 5-fold CV and evaluates AF classification quality.

Gate condition: PR-AUC >= 0.70 (mean across folds).
"""

import logging
from dataclasses import dataclass, field

import numpy as np
from omegaconf import DictConfig

from src.features.feature_matrix_builder import build_feature_matrix
from src.models.classification_trainer import train_model, get_feature_importance
from src.models.metrics import compute_classification_metrics, aggregate_fold_metrics
from src.split_generator import generate_cv_splits, save_split_index

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FoldResult:
    """Immutable result container for a single CV fold."""

    fold_idx: int
    metrics: dict[str, float]
    oof_predictions: np.ndarray
    feature_importance: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PhaseBResult:
    """Immutable result container for Phase B evaluation."""

    fold_results: list[FoldResult]
    aggregate_metrics: dict[str, float]
    gates: dict[str, bool]
    oof_predictions: np.ndarray | None = None
    feature_names: list[str] = field(default_factory=list)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_b_evaluation(cfg: DictConfig) -> PhaseBResult:
    """Run Phase B cross-validated AF classification.

    Args:
        cfg: Hydra config with model params, split config, gate thresholds.

    Returns:
        PhaseBResult with per-fold and aggregate metrics.
    """
    # 1. Build feature matrix
    x, y, groups = build_feature_matrix(cfg)
    logger.info(f"Feature matrix: {x.shape[0]} samples, {x.shape[1]} features")
    logger.info(f"Class balance: {np.mean(y):.3f} positive rate")

    # 2. Generate CV splits
    splits = generate_cv_splits(cfg, y, groups)
    save_split_index(groups, splits)

    # 3. Train and evaluate per fold
    fold_results: list[FoldResult] = []
    oof_preds = np.full(len(y), np.nan)

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        logger.info(
            f"Fold {fold_idx}: train={len(train_idx)}, val={len(val_idx)}"
        )

        x_train, x_val = x[train_idx], x[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model, probas = train_model(cfg, x_train, y_train, x_val)
        oof_preds[val_idx] = probas

        fold_metrics = compute_classification_metrics(y_val, probas)
        importance = get_feature_importance(model, list(range(x.shape[1])))

        fold_result = FoldResult(
            fold_idx=fold_idx,
            metrics=fold_metrics,
            oof_predictions=probas,
            feature_importance=importance,
        )
        fold_results.append(fold_result)

        logger.info(f"  Fold {fold_idx} PR-AUC: {fold_metrics['pr_auc']:.4f}")

    # 4. Aggregate metrics
    fold_metrics_list = [fr.metrics for fr in fold_results]
    aggregate = aggregate_fold_metrics(fold_metrics_list)

    # 5. Check gates
    gates = {
        "pr_auc": aggregate["pr_auc_mean"] >= cfg.gates.phase_b.pr_auc,
    }

    logger.info(f"Aggregate PR-AUC: {aggregate['pr_auc_mean']:.4f} "
                f"(+/- {aggregate['pr_auc_std']:.4f})")

    return PhaseBResult(
        fold_results=fold_results,
        aggregate_metrics=aggregate,
        gates=gates,
        oof_predictions=oof_preds,
    )
