"""LightGBM model trainer for sarcopenia risk prediction.

Handles training, prediction, and feature importance extraction.
Preprocessing (scaling, imputation) is fit inside this function
to prevent data leakage from train to validation sets.
"""

import logging

import lightgbm as lgb
import numpy as np
from omegaconf import DictConfig
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def train_model(
    cfg: DictConfig,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
) -> tuple[lgb.LGBMRegressor, np.ndarray]:
    """Train LightGBM model and return (model, predictions).

    Preprocessing is fit on X_train only, then applied to X_val.
    This prevents information leakage from validation data.

    Args:
        cfg: Hydra config with model.params.
        X_train: Training feature matrix.
        y_train: Training target values.
        X_val: Validation feature matrix.

    Returns:
        Tuple of (trained model, validation predictions).
    """
    # 1. Preprocessing: fit on train, transform both
    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train)
    X_val_imp = imputer.transform(X_val)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imp)
    X_val_scaled = scaler.transform(X_val_imp)

    # 2. Model training
    params = dict(cfg.model.params)
    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train_scaled,
        y_train,
    )

    # 3. Prediction on validation set
    preds = model.predict(X_val_scaled)

    return model, preds


def get_feature_importance(
    model: lgb.LGBMRegressor,
    feature_names: list[str] | None = None,
) -> dict[str, float]:
    """Extract feature importance from trained model.

    Args:
        model: Trained LightGBM model.
        feature_names: Optional list of feature names.

    Returns:
        Dictionary mapping feature name to importance score.
    """
    importances = model.feature_importances_
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(len(importances))]

    return dict(zip(feature_names, importances.tolist()))
