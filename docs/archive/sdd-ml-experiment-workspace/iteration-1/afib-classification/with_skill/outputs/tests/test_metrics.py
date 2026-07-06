"""Tests for classification metrics."""

import numpy as np
import pytest

from src.models.metrics import (
    compute_classification_metrics,
    aggregate_fold_metrics,
)


class TestComputeClassificationMetrics:
    """Tests for metric computation."""

    def test_returns_all_expected_metrics(self):
        """All expected metrics are present in result."""
        y_true = np.array([0, 0, 1, 1, 0])
        y_prob = np.array([0.1, 0.2, 0.8, 0.9, 0.3])

        metrics = compute_classification_metrics(y_true, y_prob)

        expected_keys = {"pr_auc", "roc_auc", "f1", "precision", "recall"}
        assert set(metrics.keys()) == expected_keys

    def test_metrics_are_numeric(self):
        """All metric values are float."""
        y_true = np.array([0, 0, 1, 1])
        y_prob = np.array([0.1, 0.2, 0.8, 0.9])

        metrics = compute_classification_metrics(y_true, y_prob)

        for name, value in metrics.items():
            assert isinstance(value, float), f"{name} is not float"

    def test_perfect_predictions(self):
        """Perfect predictions yield metrics close to 1.0."""
        y_true = np.array([0, 0, 1, 1])
        y_prob = np.array([0.0, 0.0, 1.0, 1.0])

        metrics = compute_classification_metrics(y_true, y_prob)

        assert metrics["roc_auc"] == 1.0
        assert metrics["f1"] == 1.0

    def test_metrics_in_valid_range(self):
        """All metrics are between 0 and 1."""
        y_true = np.array([0, 0, 1, 1, 0, 1])
        y_prob = np.array([0.3, 0.4, 0.6, 0.7, 0.5, 0.8])

        metrics = compute_classification_metrics(y_true, y_prob)

        for name, value in metrics.items():
            assert 0.0 <= value <= 1.0, f"{name}={value} out of range"


class TestAggregateFoldMetrics:
    """Tests for fold metric aggregation."""

    def test_includes_mean_and_std(self):
        """Aggregated metrics include mean and std for each metric."""
        fold_metrics = [
            {"pr_auc": 0.8, "roc_auc": 0.9},
            {"pr_auc": 0.7, "roc_auc": 0.85},
            {"pr_auc": 0.75, "roc_auc": 0.88},
        ]

        aggregated = aggregate_fold_metrics(fold_metrics)

        assert "pr_auc_mean" in aggregated
        assert "pr_auc_std" in aggregated
        assert "roc_auc_mean" in aggregated
        assert "roc_auc_std" in aggregated

    def test_mean_is_correct(self):
        """Mean computation is correct."""
        fold_metrics = [
            {"pr_auc": 0.8},
            {"pr_auc": 0.6},
        ]

        aggregated = aggregate_fold_metrics(fold_metrics)
        assert abs(aggregated["pr_auc_mean"] - 0.7) < 1e-10
