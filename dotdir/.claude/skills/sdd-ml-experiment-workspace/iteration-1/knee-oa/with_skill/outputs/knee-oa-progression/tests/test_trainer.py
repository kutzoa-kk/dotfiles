"""Tests for model trainer."""

import numpy as np
import pytest
from omegaconf import OmegaConf

from src.models.trainer import train_model


class TestTrainModel:
    """Tests for model training."""

    @pytest.fixture
    def lightgbm_config(self):
        """Config for LightGBM."""
        return OmegaConf.create({
            "model": {
                "type": "lightgbm",
                "params": {
                    "objective": "regression",
                    "n_estimators": 5,
                    "learning_rate": 0.1,
                    "max_depth": 3,
                    "num_leaves": 8,
                    "min_child_samples": 2,
                    "random_state": 42,
                    "verbose": -1,
                },
            },
        })

    @pytest.fixture
    def xgboost_config(self):
        """Config for XGBoost."""
        return OmegaConf.create({
            "model": {
                "type": "xgboost",
                "params": {
                    "objective": "reg:squarederror",
                    "n_estimators": 5,
                    "learning_rate": 0.1,
                    "max_depth": 3,
                    "random_state": 42,
                    "verbosity": 0,
                },
            },
        })

    @pytest.fixture
    def synthetic_data(self):
        """Small synthetic dataset for testing."""
        np.random.seed(42)
        n_train, n_val = 40, 10
        n_features = 5

        X_train = np.random.randn(n_train, n_features)
        y_train = np.random.randint(0, 5, n_train).astype(float)
        X_val = np.random.randn(n_val, n_features)

        return X_train, y_train, X_val

    def test_lightgbm_returns_model_and_predictions(
        self, lightgbm_config, synthetic_data
    ):
        """LightGBM training returns model and predictions."""
        X_train, y_train, X_val = synthetic_data
        model, preds = train_model(lightgbm_config, X_train, y_train, X_val)

        assert model is not None
        assert len(preds) == len(X_val)

    def test_predictions_in_valid_range(self, lightgbm_config, synthetic_data):
        """Predictions are clipped to [0, 4] range."""
        X_train, y_train, X_val = synthetic_data
        _, preds = train_model(lightgbm_config, X_train, y_train, X_val)

        assert np.all(preds >= 0.0)
        assert np.all(preds <= 4.0)

    def test_xgboost_returns_model_and_predictions(
        self, xgboost_config, synthetic_data
    ):
        """XGBoost training returns model and predictions."""
        X_train, y_train, X_val = synthetic_data
        model, preds = train_model(xgboost_config, X_train, y_train, X_val)

        assert model is not None
        assert len(preds) == len(X_val)

    def test_handles_nan_values(self, lightgbm_config):
        """Imputer handles NaN values in features."""
        np.random.seed(42)
        X_train = np.random.randn(30, 3)
        X_train[0, 0] = np.nan
        X_train[5, 1] = np.nan
        y_train = np.random.randint(0, 5, 30).astype(float)
        X_val = np.random.randn(5, 3)

        model, preds = train_model(lightgbm_config, X_train, y_train, X_val)
        assert not np.any(np.isnan(preds))

    def test_raises_on_unknown_model_type(self):
        """Raises ValueError for unknown model type."""
        cfg = OmegaConf.create({
            "model": {
                "type": "unknown_model",
                "params": {},
            },
        })
        X_train = np.random.randn(10, 3)
        y_train = np.random.randn(10)
        X_val = np.random.randn(5, 3)

        with pytest.raises(ValueError, match="Unknown model type"):
            train_model(cfg, X_train, y_train, X_val)
