"""Hold-out trainer for KL grade ordinal regression.

Trains on temporal train set (< 2024) and predicts on hold-out (>= 2024).
Used for Phase C ONE-SHOT evaluation.

Medical compliance:
    - Strict temporal separation (no future data leakage)
    - Preprocessing fit only on training data
    - Single evaluation (no iteration on holdout results)
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import lightgbm as lgb
import numpy as np
import polars as pl
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

from src.models.ordinal_trainer import DEFAULT_LGBM_PARAMS, DEFAULT_XGB_PARAMS


@dataclass(frozen=True)
class HoldoutResult:
    """Immutable hold-out training result."""

    model_type: str
    model_params: dict[str, object]
    n_train_samples: int
    n_train_patients: int
    n_holdout_samples: int
    n_holdout_patients: int
    n_features: int
    holdout_predictions: pl.DataFrame  # patient_id, side, kl_grade_true, kl_grade_pred
    feature_importance: dict[str, float] = dataclass_field(default_factory=dict)


def train_holdout_model(
    feature_matrix: pl.DataFrame,
    holdout_split: dict[str, int],
    feature_cols: list[str],
    target_col: str = "kl_grade",
    group_col: str = "patient_id",
    model_type: str = "lightgbm",
    model_params: dict | None = None,
) -> HoldoutResult:
    """Train model on train set, predict on hold-out set. ONE-SHOT.

    Temporal split: train < 2024, holdout >= 2024.
    Preprocessing is fit ONLY on training data (medical compliance).

    Args:
        feature_matrix: DataFrame with features, target, and group columns.
        holdout_split: Mapping of patient_id -> split (0=train, 1=holdout).
        feature_cols: List of feature column names.
        target_col: Target column name.
        group_col: Group column name (patient_id).
        model_type: "lightgbm" or "xgboost".
        model_params: Model parameters (defaults applied if None).

    Returns:
        HoldoutResult with predictions on hold-out set only.
    """
    if model_type == "lightgbm":
        params = {**DEFAULT_LGBM_PARAMS, **(model_params or {})}
    elif model_type == "xgboost":
        params = {**DEFAULT_XGB_PARAMS, **(model_params or {})}
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    fm = feature_matrix.with_columns(
        pl.col(group_col).cast(pl.Utf8).replace_strict(holdout_split).alias("_split")
    )

    train_df = fm.filter(pl.col("_split") == 0)
    holdout_df = fm.filter(pl.col("_split") == 1)

    x_train = train_df.select(feature_cols).to_numpy()
    y_train = train_df[target_col].to_numpy().astype(float)
    x_holdout = holdout_df.select(feature_cols).to_numpy()
    y_holdout = holdout_df[target_col].to_numpy().astype(float)

    # Fit scaler ONLY on training data (medical compliance)
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_holdout_scaled = scaler.transform(x_holdout)

    if model_type == "lightgbm":
        model = lgb.LGBMRegressor(**params)
    else:
        model = xgb.XGBRegressor(**params)

    model.fit(x_train_scaled, y_train)
    y_pred = model.predict(x_holdout_scaled)

    # Clip to valid range
    y_pred_clipped = np.clip(y_pred, 0.0, 4.0)

    # Feature importance
    fi = {}
    if hasattr(model, "feature_importances_"):
        for i, col in enumerate(feature_cols):
            fi[col] = float(model.feature_importances_[i])

    predictions = holdout_df.select([group_col, "side"]).with_columns(
        pl.Series("kl_grade_true", y_holdout),
        pl.Series("kl_grade_pred", y_pred_clipped),
    )

    return HoldoutResult(
        model_type=model_type,
        model_params=params,
        n_train_samples=train_df.shape[0],
        n_train_patients=len(train_df[group_col].unique()),
        n_holdout_samples=holdout_df.shape[0],
        n_holdout_patients=len(holdout_df[group_col].unique()),
        n_features=len(feature_cols),
        holdout_predictions=predictions,
        feature_importance=fi,
    )
