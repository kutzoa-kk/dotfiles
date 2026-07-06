"""Hold-out trainer for AF classification.

Trains a single model on train split (0) and predicts on hold-out (1).
Used for Phase C ONE-SHOT evaluation.
"""

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.models.cv_trainer import DEFAULT_LGBM_PARAMS, DEFAULT_LR_PARAMS


@dataclass(frozen=True)
class HoldoutResult:
    """Hold-out training result."""

    model_name: str
    model_params: dict[str, object]
    n_train_samples: int
    n_train_subjects: int
    n_holdout_samples: int
    n_holdout_subjects: int
    n_features: int
    n_positive_train: int
    n_positive_holdout: int
    holdout_predictions: pl.DataFrame  # record_id, af_label_true, af_prob_pred


def train_holdout_model(
    feature_matrix: pl.DataFrame,
    holdout_split: dict[str, int],
    feature_cols: list[str],
    model_type: str = "lightgbm",
    target_col: str = "af_label",
    group_col: str = "record_id",
    model_params: dict | None = None,
) -> HoldoutResult:
    """Train classifier on train set, predict on hold-out set.

    Args:
        feature_matrix: DataFrame with features, target, and group columns.
        holdout_split: Mapping of record_id -> split (0=train, 1=holdout).
        feature_cols: List of feature column names.
        model_type: "lightgbm" or "logistic_regression".
        target_col: Target column name.
        group_col: Group column name (subject ID).
        model_params: Model-specific parameters (defaults applied if None).

    Returns:
        HoldoutResult with predictions on hold-out set only.
    """
    if model_type == "lightgbm":
        default_params = DEFAULT_LGBM_PARAMS
    elif model_type == "logistic_regression":
        default_params = DEFAULT_LR_PARAMS
    else:
        raise ValueError(f"Unsupported model_type: {model_type}")

    params = {**default_params, **(model_params or {})}

    fm = feature_matrix.with_columns(
        pl.col(group_col).cast(pl.Utf8).replace_strict(holdout_split).alias("_split")
    )

    train_df = fm.filter(pl.col("_split") == 0)
    holdout_df = fm.filter(pl.col("_split") == 1)

    x_train = train_df.select(feature_cols).to_numpy()
    y_train = train_df[target_col].to_numpy()
    x_holdout = holdout_df.select(feature_cols).to_numpy()
    y_holdout = holdout_df[target_col].to_numpy()

    if model_type == "lightgbm":
        model = lgb.LGBMClassifier(**params)
        model.fit(x_train, y_train)
        y_prob = model.predict_proba(x_holdout)[:, 1]
    elif model_type == "logistic_regression":
        scaler = StandardScaler()
        x_train_scaled = scaler.fit_transform(x_train)
        x_holdout_scaled = scaler.transform(x_holdout)
        model = LogisticRegression(**params)
        model.fit(x_train_scaled, y_train)
        y_prob = model.predict_proba(x_holdout_scaled)[:, 1]

    predictions = holdout_df.select([group_col]).with_columns(
        pl.Series("af_label_true", y_holdout),
        pl.Series("af_prob_pred", y_prob),
    )

    return HoldoutResult(
        model_name=model_type,
        model_params=params,
        n_train_samples=train_df.shape[0],
        n_train_subjects=len(train_df[group_col].unique()),
        n_holdout_samples=holdout_df.shape[0],
        n_holdout_subjects=len(holdout_df[group_col].unique()),
        n_features=len(feature_cols),
        n_positive_train=int(y_train.sum()),
        n_positive_holdout=int(y_holdout.sum()),
        holdout_predictions=predictions,
    )
