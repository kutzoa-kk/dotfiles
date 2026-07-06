"""Model trainer for LightGBM / XGBoost ordinal regression.

Handles training, prediction, and feature importance extraction.
Preprocessing (scaling, imputation) is fit inside this function
to prevent data leakage from train to validation sets.

KL grade (0-4) is treated as a continuous variable for regression,
then optionally rounded/clipped for ordinal evaluation.
"""

import numpy as np
from omegaconf import DictConfig
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def train_model(
    cfg: DictConfig,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
) -> tuple:
    """Train model and return (model, predictions).

    Preprocessing is fit on X_train only, then applied to X_val.
    This prevents information leakage from validation data.

    Args:
        cfg: Hydra config with model.type and model.params.
        X_train: Training features.
        y_train: Training target (KL grade 0-4).
        X_val: Validation features.

    Returns:
        Tuple of (trained_model, predictions_on_X_val).
    """
    # 1. Preprocessing (fit on train, transform both)
    imputer = SimpleImputer(strategy="median")
    X_train_imputed = imputer.fit_transform(X_train)
    X_val_imputed = imputer.transform(X_val)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_val_scaled = scaler.transform(X_val_imputed)

    # 2. Model training
    model = _create_model(cfg)
    model.fit(X_train_scaled, y_train)

    # 3. Prediction on validation set
    predictions = model.predict(X_val_scaled)

    # 4. Clip predictions to valid KL grade range
    predictions = np.clip(predictions, 0.0, 4.0)

    return model, predictions


def _create_model(cfg: DictConfig):
    """Create model instance from config."""
    model_type = cfg.model.type
    params = dict(cfg.model.params)

    match model_type:
        case "lightgbm":
            from lightgbm import LGBMRegressor
            return LGBMRegressor(**params)
        case "xgboost":
            from xgboost import XGBRegressor
            return XGBRegressor(**params)
        case _:
            raise ValueError(f"Unknown model type: {model_type}")
