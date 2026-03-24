"""Tests for LightGBM trainer."""

import numpy as np
import pytest
from omegaconf import OmegaConf

from src.models.lgb_trainer import get_feature_importance, train_model


class TestTrainModel:
    """Tests for model training."""

    @pytest.fixture
    def training_data(self):
        """Minimal training data."""
        np.random.seed(42)
        n_train, n_val = 40, 10
        n_features = 5

        X_train = np.random.randn(n_train, n_features)
        y_train = np.random.randn(n_train)
        X_val = np.random.randn(n_val, n_features)

        return X_train, y_train, X_val

    @pytest.fixture
    def model_config(self):
        """Minimal model config."""
        return OmegaConf.create(
            {
                "model": {
                    "name": "test",
                    "type": "lightgbm",
                    "params": {
                        "n_estimators": 5,
                        "learning_rate": 0.1,
                        "max_depth": 3,
                        "num_leaves": 8,
                        "min_child_samples": 2,
                        "random_state": 42,
                        "verbose": -1,
                    },
                }
            }
        )

    def test_returns_model_and_predictions(
        self, model_config, training_data
    ):
        """Training returns a model and prediction array."""
        X_train, y_train, X_val = training_data
        model, preds = train_model(model_config, X_train, y_train, X_val)
        assert model is not None
        assert isinstance(preds, np.ndarray)
        assert len(preds) == len(X_val)

    def test_predictions_are_finite(self, model_config, training_data):
        """All predictions are finite (no NaN/Inf)."""
        X_train, y_train, X_val = training_data
        _, preds = train_model(model_config, X_train, y_train, X_val)
        assert np.all(np.isfinite(preds))

    def test_handles_missing_values(self, model_config):
        """Training handles NaN values in input."""
        np.random.seed(42)
        X_train = np.random.randn(40, 5)
        X_train[0, 0] = np.nan
        X_train[5, 2] = np.nan
        y_train = np.random.randn(40)
        X_val = np.random.randn(10, 5)

        model, preds = train_model(model_config, X_train, y_train, X_val)
        assert np.all(np.isfinite(preds))


class TestGetFeatureImportance:
    """Tests for feature importance extraction."""

    @pytest.fixture
    def model_config(self):
        """Minimal model config."""
        return OmegaConf.create(
            {
                "model": {
                    "name": "test",
                    "type": "lightgbm",
                    "params": {
                        "n_estimators": 5,
                        "learning_rate": 0.1,
                        "max_depth": 3,
                        "num_leaves": 8,
                        "min_child_samples": 2,
                        "random_state": 42,
                        "verbose": -1,
                    },
                }
            }
        )

    def test_returns_dict(self, model_config):
        """Feature importance is returned as dict."""
        np.random.seed(42)
        X_train = np.random.randn(40, 3)
        y_train = np.random.randn(40)
        X_val = np.random.randn(10, 3)

        model, _ = train_model(model_config, X_train, y_train, X_val)
        importance = get_feature_importance(
            model, feature_names=["f1", "f2", "f3"]
        )
        assert isinstance(importance, dict)
        assert len(importance) == 3

    def test_generates_names_when_none(self, model_config):
        """Auto-generates feature names when not provided."""
        np.random.seed(42)
        X_train = np.random.randn(40, 3)
        y_train = np.random.randn(40)
        X_val = np.random.randn(10, 3)

        model, _ = train_model(model_config, X_train, y_train, X_val)
        importance = get_feature_importance(model)
        assert "feature_0" in importance
