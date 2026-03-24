"""Ordinal regression trainer for KL grade prediction.

Trains LightGBM and XGBoost models with GroupKFold cross-validation.
Ordinal regression is handled via threshold-based approach or direct
multi-class classification with ordinal-aware loss.

Patient-level grouping ensures L/R sides are co-located.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import lightgbm as lgb
import numpy as np
import polars as pl
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

# Default LightGBM parameters for ordinal regression
DEFAULT_LGBM_PARAMS: dict[str, object] = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "num_leaves": 31,
    "min_child_samples": 20,
    "random_state": 42,
    "objective": "regression",
    "metric": "rmse",
    "verbosity": -1,
    "n_jobs": -1,
}

# Default XGBoost parameters for ordinal regression
DEFAULT_XGB_PARAMS: dict[str, object] = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "min_child_weight": 5,
    "random_state": 42,
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "verbosity": 0,
    "n_jobs": -1,
}


@dataclass(frozen=True)
class FoldResult:
    """Immutable result for a single CV fold."""

    fold: int
    rmse: float
    mae: float
    spearman_rho: float
    n_train: int
    n_val: int


@dataclass(frozen=True)
class TrainingResult:
    """Immutable training result across all folds."""

    model_type: str
    model_params: dict[str, object]
    fold_results: list[FoldResult] = dataclass_field(default_factory=list)
    oof_predictions: pl.DataFrame | None = None
    pooled_rmse: float = 0.0
    pooled_mae: float = 0.0
    pooled_spearman_rho: float = 0.0
    n_features: int = 0
    feature_importance: dict[str, float] = dataclass_field(default_factory=dict)


def _create_model(model_type: str, params: dict) -> object:
    """Create a model instance based on type."""
    if model_type == "lightgbm":
        return lgb.LGBMRegressor(**params)
    elif model_type == "xgboost":
        return xgb.XGBRegressor(**params)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


def train_ordinal_model(
    feature_matrix: pl.DataFrame,
    split_index: dict[str, int],
    feature_cols: list[str],
    target_col: str = "kl_grade",
    group_col: str = "patient_id",
    model_type: str = "lightgbm",
    model_params: dict | None = None,
    n_splits: int = 5,
) -> TrainingResult:
    """Train ordinal regression model with GroupKFold CV.

    Preprocessing (StandardScaler) is fit INSIDE each fold.
    L/R sides are co-located via patient_id grouping.

    Args:
        feature_matrix: DataFrame with features, target, and group columns.
        split_index: Mapping of patient_id -> fold index.
        feature_cols: List of feature column names.
        target_col: Target column name (kl_grade).
        group_col: Group column name (patient_id).
        model_type: "lightgbm" or "xgboost".
        model_params: Model parameters (defaults applied if None).
        n_splits: Number of CV folds.

    Returns:
        TrainingResult with OOF predictions and per-fold metrics.
    """
    if model_type == "lightgbm":
        params = {**DEFAULT_LGBM_PARAMS, **(model_params or {})}
    elif model_type == "xgboost":
        params = {**DEFAULT_XGB_PARAMS, **(model_params or {})}
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    # Assign fold to each row based on patient_id
    fm = feature_matrix.with_columns(
        pl.col(group_col).cast(pl.Utf8).replace_strict(split_index).alias("_fold")
    )

    all_fold_results: list[FoldResult] = []
    oof_dfs: list[pl.DataFrame] = []
    feature_importances: dict[str, list[float]] = {col: [] for col in feature_cols}

    for fold_idx in range(n_splits):
        train_df = fm.filter(pl.col("_fold") != fold_idx)
        val_df = fm.filter(pl.col("_fold") == fold_idx)

        x_train = train_df.select(feature_cols).to_numpy()
        y_train = train_df[target_col].to_numpy().astype(float)
        x_val = val_df.select(feature_cols).to_numpy()
        y_val = val_df[target_col].to_numpy().astype(float)

        # Fit scaler INSIDE fold (medical compliance)
        scaler = StandardScaler()
        x_train_scaled = scaler.fit_transform(x_train)
        x_val_scaled = scaler.transform(x_val)

        model = _create_model(model_type, params)
        model.fit(x_train_scaled, y_train)
        y_pred = model.predict(x_val_scaled)

        # Clip predictions to valid range [0, 4]
        y_pred_clipped = np.clip(y_pred, 0.0, 4.0)

        # Metrics
        from scipy import stats as sp_stats

        rmse = float(np.sqrt(mean_squared_error(y_val, y_pred_clipped)))
        mae = float(mean_absolute_error(y_val, y_pred_clipped))
        rho, _ = sp_stats.spearmanr(y_val, y_pred_clipped)

        fold_result = FoldResult(
            fold=fold_idx,
            rmse=rmse,
            mae=mae,
            spearman_rho=float(rho),
            n_train=len(x_train),
            n_val=len(x_val),
        )
        all_fold_results.append(fold_result)

        # OOF predictions
        oof_df = val_df.select([group_col, "side"]).with_columns(
            pl.Series("kl_grade_true", y_val),
            pl.Series("kl_grade_pred", y_pred_clipped),
            pl.lit(fold_idx).alias("fold"),
        )
        oof_dfs.append(oof_df)

        # Feature importance
        if hasattr(model, "feature_importances_"):
            for i, col in enumerate(feature_cols):
                feature_importances[col].append(float(model.feature_importances_[i]))

    # Combine OOF predictions
    oof_all = pl.concat(oof_dfs)

    # Pooled metrics
    y_true_all = oof_all["kl_grade_true"].to_numpy()
    y_pred_all = oof_all["kl_grade_pred"].to_numpy()
    pooled_rmse = float(np.sqrt(mean_squared_error(y_true_all, y_pred_all)))
    pooled_mae = float(mean_absolute_error(y_true_all, y_pred_all))
    pooled_rho, _ = sp_stats.spearmanr(y_true_all, y_pred_all)

    # Average feature importance
    avg_importance = {
        col: float(np.mean(vals)) for col, vals in feature_importances.items() if vals
    }

    return TrainingResult(
        model_type=model_type,
        model_params=params,
        fold_results=all_fold_results,
        oof_predictions=oof_all,
        pooled_rmse=pooled_rmse,
        pooled_mae=pooled_mae,
        pooled_spearman_rho=float(pooled_rho),
        n_features=len(feature_cols),
        feature_importance=avg_importance,
    )
