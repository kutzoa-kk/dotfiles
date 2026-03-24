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

    def test_perfect_correlation(self):
        """Perfect predictions yield rho = 1.0."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        metrics = compute_metrics(y_true, y_pred)
        assert metrics["spearman_rho"] == pytest.approx(1.0)
        assert metrics["rmse"] == pytest.approx(0.0)

    def test_returns_expected_keys(self):
        """Metrics dict contains all expected keys."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.2, 2.8])
        metrics = compute_metrics(y_true, y_pred)
        expected_keys = {"spearman_rho", "spearman_p_value", "rmse", "mae"}
        assert set(metrics.keys()) == expected_keys

    def test_all_values_are_float(self):
        """All metric values are numeric."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 2.5])
        metrics = compute_metrics(y_true, y_pred)
        for name, value in metrics.items():
            assert isinstance(value, float), f"{name} is not float"


class TestAggregateFoldMetrics:
    """Tests for fold metric aggregation."""

    def test_computes_mean_and_std(self):
        """Aggregation produces mean and std for each metric."""
        fold_results = [
            FoldResult(
                fold_idx=0,
                metrics={"rho": 0.5, "rmse": 1.0},
                oof_predictions=np.array([]),
            ),
            FoldResult(
                fold_idx=1,
                metrics={"rho": 0.7, "rmse": 0.8},
                oof_predictions=np.array([]),
            ),
        ]
        agg = aggregate_fold_metrics(fold_results)
        assert "rho_mean" in agg
        assert "rho_std" in agg
        assert "rmse_mean" in agg
        assert agg["rho_mean"] == pytest.approx(0.6)


class TestPhaseBResult:
    """Tests for PhaseBResult dataclass."""

    def test_all_gates_passed_when_true(self):
        """all_gates_passed returns True when all gates pass."""
        result = PhaseBResult(
            fold_results=[],
            aggregate_metrics={},
            gates={"spearman_rho": True},
        )
        assert result.all_gates_passed is True

    def test_all_gates_passed_when_false(self):
        """all_gates_passed returns False when any gate fails."""
        result = PhaseBResult(
            fold_results=[],
            aggregate_metrics={},
            gates={"spearman_rho": False},
        )
        assert result.all_gates_passed is False
