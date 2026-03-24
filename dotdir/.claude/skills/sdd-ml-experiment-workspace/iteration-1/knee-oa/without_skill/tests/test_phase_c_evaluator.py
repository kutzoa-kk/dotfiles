"""Tests for Phase C evaluator -- hold-out ONE-SHOT evaluation."""

import numpy as np
import polars as pl
import pytest

from src.models.holdout_trainer import HoldoutResult
from src.models.phase_c_evaluator import HoldoutEvaluation, evaluate_holdout


@pytest.fixture
def good_holdout_result() -> HoldoutResult:
    """Holdout result with good performance."""
    n = 50
    np.random.seed(42)
    y_true = np.repeat([0, 1, 2, 3, 4], 10).astype(float)
    y_pred = y_true + np.random.normal(0, 0.3, n)
    y_pred = np.clip(y_pred, 0, 4)

    preds = pl.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "side": ["L", "R"] * 25,
        "kl_grade_true": y_true.tolist(),
        "kl_grade_pred": y_pred.tolist(),
    })

    return HoldoutResult(
        model_type="lightgbm",
        model_params={"n_estimators": 500},
        n_train_samples=200,
        n_train_patients=100,
        n_holdout_samples=n,
        n_holdout_patients=25,
        n_features=15,
        holdout_predictions=preds,
    )


@pytest.fixture
def poor_holdout_result() -> HoldoutResult:
    """Holdout result with poor performance."""
    n = 50
    np.random.seed(99)
    y_true = np.repeat([0, 1, 2, 3, 4], 10).astype(float)
    y_pred = np.random.uniform(0, 4, n)  # Random

    preds = pl.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "side": ["L", "R"] * 25,
        "kl_grade_true": y_true.tolist(),
        "kl_grade_pred": y_pred.tolist(),
    })

    return HoldoutResult(
        model_type="lightgbm",
        model_params={"n_estimators": 500},
        n_train_samples=200,
        n_train_patients=100,
        n_holdout_samples=n,
        n_holdout_patients=25,
        n_features=15,
        holdout_predictions=preds,
    )


class TestEvaluateHoldout:
    def test_returns_holdout_evaluation(
        self, good_holdout_result: HoldoutResult
    ) -> None:
        result = evaluate_holdout(good_holdout_result)
        assert isinstance(result, HoldoutEvaluation)

    def test_gate_pass_good_result(
        self, good_holdout_result: HoldoutResult
    ) -> None:
        result = evaluate_holdout(good_holdout_result)
        assert result.gate_passed is True
        assert result.rmse <= 1.0
        assert result.spearman_rho >= 0.5

    def test_gate_fail_poor_result(
        self, poor_holdout_result: HoldoutResult
    ) -> None:
        result = evaluate_holdout(poor_holdout_result)
        assert result.gate_passed is False

    def test_has_confidence_intervals(
        self, good_holdout_result: HoldoutResult
    ) -> None:
        """Medical compliance: CIs are required."""
        result = evaluate_holdout(good_holdout_result)
        assert result.ci_rmse_lower < result.rmse
        assert result.ci_rmse_upper > result.rmse
        assert result.ci_rho_lower < result.spearman_rho
        assert result.ci_rho_upper > result.spearman_rho

    def test_has_baseline_comparison(
        self, good_holdout_result: HoldoutResult
    ) -> None:
        result = evaluate_holdout(good_holdout_result)
        assert result.baseline_rmse > 0
        assert result.rmse_improvement > 0  # Model should beat mean predictor

    def test_has_adjacent_accuracy(
        self, good_holdout_result: HoldoutResult
    ) -> None:
        result = evaluate_holdout(good_holdout_result)
        assert 0.0 <= result.adjacent_accuracy <= 1.0

    def test_one_shot_description(
        self, good_holdout_result: HoldoutResult
    ) -> None:
        result = evaluate_holdout(good_holdout_result)
        assert "ONE-SHOT" in result.description
