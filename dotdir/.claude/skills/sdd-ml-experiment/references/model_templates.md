# Model Templates (src/models/)

Generate evaluator and trainer modules for each experiment phase.

## Common Result Pattern

All evaluators return a result dataclass — never print results directly.

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PhaseResult:
    """Immutable result container for a phase evaluation."""

    metrics: dict[str, float]
    gates: dict[str, bool]
    details: dict = field(default_factory=dict)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())
```

## Phase A Evaluator Template

Phase A validates the target construct itself — before any prediction modeling.

```python
"""Phase A evaluator: {{phase_a_name}}.

Validates:
{{For each validation:}}
- {{validation_description}}
"""

import logging

import polars as pl
from omegaconf import DictConfig
from scipy import stats

from src.data_access import load_data
from src.schema.leakage_check import check_feature_leakage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseAResult:
    metrics: dict[str, float]
    gates: dict[str, bool]
    details: dict = field(default_factory=dict)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_a_evaluation(cfg: DictConfig) -> PhaseAResult:
    """Run Phase A validation checks.

    Args:
        cfg: Hydra config with data paths, thresholds, etc.

    Returns:
        PhaseAResult with metrics and gate pass/fail status.
    """
    # 1. Load data
    df = load_data(cfg)

    # 2. Compute target construct
    # {{target_computation — e.g., GCRS scores}}

    # 3. Validate construct
    metrics = {}
    gates = {}

    # Example: correlation between target and expected correlate
    # rho, p_value = stats.spearmanr(df["target"], df["expected_correlate"])
    # metrics["spearman_rho"] = rho
    # gates["spearman_rho"] = rho >= cfg.gates.phase_a.min_rho

    # Example: batch effect check (no significant difference between groups)
    # stat, p_value = stats.mannwhitneyu(group_a, group_b)
    # metrics["batch_effect_p"] = p_value
    # gates["no_batch_effect"] = p_value > 0.05

    return PhaseAResult(metrics=metrics, gates=gates)
```

## Phase B Evaluator Template

Phase B runs cross-validated prediction and evaluates model performance.

```python
"""Phase B evaluator: {{phase_b_name}}.

Trains {{model_type}} with {{cv_strategy}} and evaluates prediction quality.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import polars as pl
from omegaconf import DictConfig

from src.models.{{trainer_module}} import train_model
from src.features.feature_matrix_builder import build_feature_matrix
from src.split_generator import generate_splits

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FoldResult:
    fold_idx: int
    metrics: dict[str, float]
    oof_predictions: np.ndarray
    feature_importance: dict[str, float] | None = None


@dataclass(frozen=True)
class PhaseBResult:
    fold_results: list[FoldResult]
    aggregate_metrics: dict[str, float]
    gates: dict[str, bool]
    oof_predictions: np.ndarray | None = None

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_b_evaluation(cfg: DictConfig) -> PhaseBResult:
    """Run Phase B cross-validated prediction.

    Args:
        cfg: Hydra config with model params, split config, gate thresholds.

    Returns:
        PhaseBResult with per-fold and aggregate metrics.
    """
    # 1. Build feature matrix
    X, y, groups = build_feature_matrix(cfg)

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
        fold_results.append(FoldResult(
            fold_idx=fold_idx,
            metrics=fold_metrics,
            oof_predictions=preds,
        ))

    # 4. Aggregate metrics
    aggregate = aggregate_fold_metrics(fold_results)

    # 5. Check gates
    gates = {}
    # Example: gates["spearman_rho"] = aggregate["spearman_rho"] >= cfg.gates.phase_b.min_rho

    return PhaseBResult(
        fold_results=fold_results,
        aggregate_metrics=aggregate,
        gates=gates,
        oof_predictions=oof_preds,
    )
```

## Phase C Evaluator Template

Phase C is the one-shot holdout evaluation.

```python
"""Phase C evaluator: Holdout evaluation (ONE-SHOT).

This module runs exactly once on the held-out test set.
Re-running after seeing results constitutes p-hacking.
"""

import logging
from dataclasses import dataclass, field

from omegaconf import DictConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseCResult:
    metrics: dict[str, float]
    gates: dict[str, bool]
    holdout_run_count: int = 1  # Track how many times holdout was evaluated

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_c_evaluation(cfg: DictConfig) -> PhaseCResult:
    """Run one-shot holdout evaluation.

    WARNING: This function should be called AT MOST ONCE per experiment.
    """
    # 1. Load best model from Phase B
    # 2. Load holdout data
    # 3. Predict and evaluate
    # 4. Return results (do NOT iterate)

    metrics = {}
    gates = {}

    return PhaseCResult(metrics=metrics, gates=gates)
```

## Trainer Template

The trainer is a focused module that handles model training mechanics.

```python
"""Model trainer for {{model_type}}.

Handles training, prediction, and feature importance extraction.
Preprocessing (scaling, imputation) is fit inside this function
to prevent data leakage from train to validation sets.
"""

import numpy as np
from omegaconf import DictConfig


def train_model(
    cfg: DictConfig,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
) -> tuple:
    """Train model and return (model, predictions).

    Preprocessing is fit on X_train only, then applied to X_val.
    This prevents information leakage from validation data.
    """
    # 1. Preprocessing (fit on train, transform both)
    # 2. Model training
    # 3. Prediction on validation set
    # 4. Return (model, predictions)
    raise NotImplementedError("Implement training logic")
```
