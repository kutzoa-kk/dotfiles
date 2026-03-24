"""Model trainer for AF classification.

Handles training, prediction, and feature importance extraction
for LightGBM and Logistic Regression classifiers.
Preprocessing (scaling, imputation) is fit inside this function
to prevent data leakage from train to validation sets.
"""

import logging

import numpy as np
from omegaconf import DictConfig
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def train_model(
    cfg: DictConfig,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
) -> tuple:
    """Train classifier and return (model, predicted_probabilities).

    Preprocessing is fit on x_train only, then applied to x_val.
    This prevents information leakage from validation data.

    Args:
        cfg: Config with model.type and model.params.
        x_train: Training features.
        y_train: Training labels.
        x_val: Validation features.

    Returns:
        Tuple of (trained_model, predicted_probabilities_for_positive_class).

    Raises:
        ValueError: If model type is unknown.
    """
    # 1. Preprocessing (fit on train, transform both)
    imputer = SimpleImputer(strategy="median")
    x_train_imp = imputer.fit_transform(x_train)
    x_val_imp = imputer.transform(x_val)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_imp)
    x_val_scaled = scaler.transform(x_val_imp)

    # 2. Model training
    model = _create_model(cfg)
    model.fit(x_train_scaled, y_train)

    # 3. Prediction (probability of positive class)
    probas = model.predict_proba(x_val_scaled)[:, 1]

    return model, probas


def _create_model(cfg: DictConfig):
    """Create model instance based on config.

    Args:
        cfg: Config with model.type and model.params.

    Returns:
        Instantiated sklearn-compatible classifier.

    Raises:
        ValueError: If model type is unknown.
    """
    params = dict(cfg.model.params)

    match cfg.model.type:
        case "lightgbm":
            import lightgbm as lgb
            return lgb.LGBMClassifier(**params)
        case "logistic_regression":
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(**params)
        case _:
            raise ValueError(f"Unknown model type: {cfg.model.type}")


def get_feature_importance(model, feature_names: list[str]) -> dict[str, float]:
    """Extract feature importance from trained model.

    Args:
        model: Trained model.
        feature_names: List of feature names.

    Returns:
        Dictionary mapping feature names to importance values.
    """
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        logger.warning("Model does not expose feature importances")
        return {}

    return dict(zip(feature_names, importances))
