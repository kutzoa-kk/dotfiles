"""Tests for classification trainer."""

import numpy as np
import pytest
from omegaconf import OmegaConf

from src.models.classification_trainer import train_model, get_feature_importance


class TestTrainModel:
    """Tests for the train_model function."""

    def test_returns_model_and_predictions(self, sample_config):
        """train_model returns (model, predictions) tuple."""
        np.random.seed(42)
        x_train = np.random.randn(40, 10)
        y_train = np.random.choice([0, 1], 40)
        x_val = np.random.randn(10, 10)

        model, preds = train_model(sample_config, x_train, y_train, x_val)
        assert model is not None
        assert isinstance(preds, np.ndarray)

    def test_predictions_are_probabilities(self, sample_config):
        """Predictions are probabilities in [0, 1]."""
        np.random.seed(42)
        x_train = np.random.randn(40, 10)
        y_train = np.random.choice([0, 1], 40)
        x_val = np.random.randn(10, 10)

        _, preds = train_model(sample_config, x_train, y_train, x_val)
        assert np.all(preds >= 0)
        assert np.all(preds <= 1)

    def test_prediction_length_matches_validation(self, sample_config):
        """Number of predictions matches validation set size."""
        np.random.seed(42)
        x_train = np.random.randn(40, 10)
        y_train = np.random.choice([0, 1], 40)
        x_val = np.random.randn(10, 10)

        _, preds = train_model(sample_config, x_train, y_train, x_val)
        assert len(preds) == len(x_val)

    def test_logistic_regression_model(self):
        """Logistic regression model trains successfully."""
        cfg = OmegaConf.create({
            "model": {
                "name": "logistic_regression",
                "type": "logistic_regression",
                "params": {
                    "C": 1.0,
                    "penalty": "l2",
                    "solver": "lbfgs",
                    "max_iter": 100,
                    "random_state": 42,
                },
            },
        })
        np.random.seed(42)
        x_train = np.random.randn(40, 5)
        y_train = np.random.choice([0, 1], 40)
        x_val = np.random.randn(10, 5)

        model, preds = train_model(cfg, x_train, y_train, x_val)
        assert model is not None
        assert len(preds) == 10

    def test_unknown_model_raises(self):
        """Unknown model type raises ValueError."""
        cfg = OmegaConf.create({
            "model": {
                "type": "unknown_model",
                "params": {},
            },
        })
        with pytest.raises(ValueError, match="Unknown model type"):
            train_model(cfg, np.zeros((10, 5)), np.zeros(10), np.zeros((5, 5)))


class TestGetFeatureImportance:
    """Tests for feature importance extraction."""

    def test_returns_dict(self, sample_config):
        """Feature importance returns a dictionary."""
        np.random.seed(42)
        x_train = np.random.randn(40, 5)
        y_train = np.random.choice([0, 1], 40)
        x_val = np.random.randn(10, 5)

        model, _ = train_model(sample_config, x_train, y_train, x_val)
        importance = get_feature_importance(model, ["f1", "f2", "f3", "f4", "f5"])
        assert isinstance(importance, dict)
        assert len(importance) == 5
