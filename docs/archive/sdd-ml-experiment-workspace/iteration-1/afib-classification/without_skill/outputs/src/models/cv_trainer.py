"""CV trainers for AF classification with StratifiedGroupKFold.

Trains LightGBM and Logistic Regression classifiers using split_index
(record_id -> fold) for data splitting to prevent data leakage.
"""

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler

DEFAULT_LGBM_PARAMS: dict = {
    "n_estimators": 100,
    "learning_rate": 0.1,
    "max_depth": 6,
    "num_leaves": 31,
    "random_state": 42,
    "objective": "binary",
    "metric": "average_precision",
    "verbosity": -1,
    "is_unbalance": True,
}

DEFAULT_LR_PARAMS: dict = {
    "C": 1.0,
    "penalty": "l2",
    "solver": "lbfgs",
    "max_iter": 1000,
    "random_state": 42,
}


@dataclass(frozen=True)
class FoldResult:
    """Per-fold training result."""

    fold: int
    pr_auc: float
    roc_auc: float
    n_train: int
    n_test: int
    n_positive_train: int
    n_positive_test: int


@dataclass(frozen=True)
class CVTrainingResult:
    """Overall CV training result with OOF predictions."""

    model_name: str
    fold_results: list[FoldResult]
    oof_predictions: pl.DataFrame  # record_id, af_label_true, af_prob_pred
    pooled_pr_auc: float
    pooled_roc_auc: float


def _train_lgbm_fold(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    params: dict,
) -> np.ndarray:
    """Train LightGBM on one fold, return predicted probabilities."""
    model = lgb.LGBMClassifier(**params)
    model.fit(x_train, y_train)
    return model.predict_proba(x_test)[:, 1]


def _train_lr_fold(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    params: dict,
) -> np.ndarray:
    """Train Logistic Regression on one fold, return predicted probabilities.

    Preprocessing (StandardScaler) is fit INSIDE the fold to prevent leakage.
    """
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    model = LogisticRegression(**params)
    model.fit(x_train_scaled, y_train)
    return model.predict_proba(x_test_scaled)[:, 1]


def train_cv_model(
    feature_matrix: pl.DataFrame,
    split_index: dict[str, int],
    feature_cols: list[str],
    model_type: str = "lightgbm",
    target_col: str = "af_label",
    group_col: str = "record_id",
    model_params: dict | None = None,
) -> CVTrainingResult:
    """Train classifier with StratifiedGroupKFold CV.

    Uses split_index (record_id -> fold) for data splitting.
    Returns OOF predictions and per-fold metrics.

    Args:
        feature_matrix: DataFrame with features, target, and group columns.
        split_index: Mapping of record_id -> fold index.
        feature_cols: List of feature column names for training.
        model_type: "lightgbm" or "logistic_regression".
        target_col: Target column name.
        group_col: Group column name (subject ID).
        model_params: Model-specific parameters (defaults applied if None).

    Returns:
        CVTrainingResult with fold results and OOF predictions.
    """
    if model_type == "lightgbm":
        default_params = DEFAULT_LGBM_PARAMS
        train_fn = _train_lgbm_fold
    elif model_type == "logistic_regression":
        default_params = DEFAULT_LR_PARAMS
        train_fn = _train_lr_fold
    else:
        raise ValueError(f"Unsupported model_type: {model_type}")

    params = {**default_params, **(model_params or {})}

    # Assign fold to each row
    fm = feature_matrix.with_columns(
        pl.col(group_col).cast(pl.Utf8).replace_strict(split_index).alias("fold")
    )

    n_folds = max(split_index.values()) + 1
    fold_results: list[FoldResult] = []
    oof_parts: list[pl.DataFrame] = []

    for fold_idx in range(n_folds):
        train_mask = fm["fold"] != fold_idx
        test_mask = fm["fold"] == fold_idx

        train_df = fm.filter(train_mask)
        test_df = fm.filter(test_mask)

        if test_df.shape[0] == 0:
            continue

        x_train = train_df.select(feature_cols).to_numpy()
        y_train = train_df[target_col].to_numpy()
        x_test = test_df.select(feature_cols).to_numpy()
        y_test = test_df[target_col].to_numpy()

        y_prob = train_fn(x_train, y_train, x_test, params)

        pr_auc = float(average_precision_score(y_test, y_prob))
        # ROC-AUC as secondary
        from sklearn.metrics import roc_auc_score
        roc_auc = float(roc_auc_score(y_test, y_prob))

        fold_results.append(
            FoldResult(
                fold=fold_idx,
                pr_auc=pr_auc,
                roc_auc=roc_auc,
                n_train=train_df.shape[0],
                n_test=test_df.shape[0],
                n_positive_train=int(y_train.sum()),
                n_positive_test=int(y_test.sum()),
            )
        )

        oof_part = test_df.select([group_col]).with_columns(
            pl.Series("af_label_true", y_test),
            pl.Series("af_prob_pred", y_prob),
        )
        oof_parts.append(oof_part)

    oof_predictions = pl.concat(oof_parts)

    # Pooled metrics across all OOF predictions
    y_true_all = oof_predictions["af_label_true"].to_numpy()
    y_prob_all = oof_predictions["af_prob_pred"].to_numpy()
    pooled_pr_auc = float(average_precision_score(y_true_all, y_prob_all))

    from sklearn.metrics import roc_auc_score
    pooled_roc_auc = float(roc_auc_score(y_true_all, y_prob_all))

    return CVTrainingResult(
        model_name=model_type,
        fold_results=fold_results,
        oof_predictions=oof_predictions,
        pooled_pr_auc=pooled_pr_auc,
        pooled_roc_auc=pooled_roc_auc,
    )
