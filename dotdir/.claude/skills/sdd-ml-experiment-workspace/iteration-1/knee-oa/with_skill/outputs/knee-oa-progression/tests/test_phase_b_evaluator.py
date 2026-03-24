"""Tests for Phase B evaluator."""

import numpy as np
import pytest

from src.models.phase_b_evaluator import (
    FoldResult,
    PhaseBResult,
    aggregate_fold_metrics,
    compute_metrics,
)


class TestComputeMetrics:
    """Tests for metric computation."""

    def test_perfect_predictions(self):
        """Perfect predictions give RMSE=0 and accuracy=1."""
        y_true = np.array([0, 1, 2, 3, 4])
        y_pred = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        metrics = compute_metrics(y_true, y_pred)

        assert metrics["rmse"] == pytest.approx(0.0, abs=1e-6)
        assert metrics["mae"] == pytest.approx(0.0, abs=1e-6)
        assert metrics["exact_accuracy"] == pytest.approx(1.0)
        assert metrics["ordinal_accuracy_within_1"] == pytest.approx(1.0)

    def test_one_grade_error(self):
        """Predictions off by 1 grade give ordinal accuracy = 1."""
        y_true = np.array([0, 1, 2, 3, 4])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 3.0])
        metrics = compute_metrics(y_true, y_pred)

        assert metrics["rmse"] == pytest.approx(1.0)
        assert metrics["ordinal_accuracy_within_1"] == pytest.approx(1.0)
        assert metrics["exact_accuracy"] == pytest.approx(0.0)

    def test_large_errors(self):
        """Large errors produce low ordinal accuracy."""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([4.0, 4.0, 4.0])
        metrics = compute_metrics(y_true, y_pred)

        assert metrics["rmse"] == pytest.approx(4.0)
        assert metrics["ordinal_accuracy_within_1"] == pytest.approx(0.0)

    def test_returns_all_expected_metrics(self):
        """Metric dict contains all expected keys."""
        y_true = np.array([1, 2, 3])
        y_pred = np.array([1.5, 2.5, 2.5])
        metrics = compute_metrics(y_true, y_pred)

        expected_keys = {"rmse", "mae", "ordinal_accuracy_within_1", "exact_accuracy"}
        assert set(metrics.keys()) == expected_keys


class TestAggregateFoldMetrics:
    """Tests for fold metric aggregation."""

    def test_computes_mean_and_std(self):
        """Aggregation produces mean and std for each metric."""
        fold_results = [
            FoldResult(fold_idx=0, metrics={"rmse": 1.0, "mae": 0.5}, oof_predictions=np.array([])),
            FoldResult(fold_idx=1, metrics={"rmse": 1.2, "mae": 0.6}, oof_predictions=np.array([])),
            FoldResult(fold_idx=2, metrics={"rmse": 0.8, "mae": 0.4}, oof_predictions=np.array([])),
        ]
        agg = aggregate_fold_metrics(fold_results)

        assert "rmse_mean" in agg
        assert "rmse_std" in agg
        assert "mae_mean" in agg
        assert agg["rmse_mean"] == pytest.approx(1.0)


class TestPhaseBResult:
    """Tests for PhaseBResult dataclass."""

    def test_all_gates_passed(self):
        """all_gates_passed returns True when all gates pass."""
        result = PhaseBResult(
            fold_results=[],
            aggregate_metrics={"rmse_mean": 0.8},
            gates={"rmse": True},
        )
        assert result.all_gates_passed is True

    def test_gate_failure(self):
        """all_gates_passed returns False when gate fails."""
        result = PhaseBResult(
            fold_results=[],
            aggregate_metrics={"rmse_mean": 1.5},
            gates={"rmse": False},
        )
        assert result.all_gates_passed is False
