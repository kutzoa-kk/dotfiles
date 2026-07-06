"""Tests for Phase B evaluator -- OOF prediction evaluation."""

import numpy as np
import polars as pl
import pytest

from src.models.ordinal_trainer import FoldResult, TrainingResult
from src.models.phase_b_evaluator import (
    compute_confusion_matrix,
    compute_ordinal_metrics,
    evaluate_phase_b,
)
from src.models.phase_a_evaluator import EvaluationReport


@pytest.fixture
def good_training_result() -> TrainingResult:
    """Training result with good performance (RMSE < 1.0)."""
    n = 100
    np.random.seed(42)
    y_true = np.repeat([0, 1, 2, 3, 4], 20).astype(float)
    y_pred = y_true + np.random.normal(0, 0.3, n)
    y_pred = np.clip(y_pred, 0, 4)

    oof = pl.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "side": ["L", "R"] * 50,
        "kl_grade_true": y_true.tolist(),
        "kl_grade_pred": y_pred.tolist(),
        "fold": ([0] * 20 + [1] * 20 + [2] * 20 + [3] * 20 + [4] * 20),
    })

    fold_results = []
    for fold_idx in range(5):
        mask = oof.filter(pl.col("fold") == fold_idx)
        yt = mask["kl_grade_true"].to_numpy()
        yp = mask["kl_grade_pred"].to_numpy()
        from scipy import stats
        rho, _ = stats.spearmanr(yt, yp)
        rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
        mae = float(np.mean(np.abs(yt - yp)))
        fold_results.append(FoldResult(
            fold=fold_idx, rmse=rmse, mae=mae,
            spearman_rho=float(rho), n_train=80, n_val=20,
        ))

    from scipy import stats
    pooled_rho, _ = stats.spearmanr(y_true, y_pred)

    return TrainingResult(
        model_type="lightgbm",
        model_params={"n_estimators": 100},
        fold_results=fold_results,
        oof_predictions=oof,
        pooled_rmse=float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        pooled_mae=float(np.mean(np.abs(y_true - y_pred))),
        pooled_spearman_rho=float(pooled_rho),
        n_features=10,
    )


@pytest.fixture
def poor_training_result() -> TrainingResult:
    """Training result with poor performance (RMSE > 1.0)."""
    n = 100
    np.random.seed(99)
    y_true = np.repeat([0, 1, 2, 3, 4], 20).astype(float)
    y_pred = np.random.uniform(0, 4, n)  # Random predictions

    oof = pl.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "side": ["L", "R"] * 50,
        "kl_grade_true": y_true.tolist(),
        "kl_grade_pred": y_pred.tolist(),
        "fold": ([0] * 20 + [1] * 20 + [2] * 20 + [3] * 20 + [4] * 20),
    })

    from scipy import stats
    pooled_rho, _ = stats.spearmanr(y_true, y_pred)

    return TrainingResult(
        model_type="lightgbm",
        model_params={"n_estimators": 100},
        fold_results=[
            FoldResult(fold=i, rmse=1.5, mae=1.2, spearman_rho=0.1, n_train=80, n_val=20)
            for i in range(5)
        ],
        oof_predictions=oof,
        pooled_rmse=float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        pooled_mae=float(np.mean(np.abs(y_true - y_pred))),
        pooled_spearman_rho=float(pooled_rho),
        n_features=10,
    )


class TestEvaluatePhaseB:
    def test_returns_evaluation_report(
        self, good_training_result: TrainingResult
    ) -> None:
        result = evaluate_phase_b(good_training_result)
        assert isinstance(result, EvaluationReport)

    def test_gate_pass_good_result(
        self, good_training_result: TrainingResult
    ) -> None:
        result = evaluate_phase_b(good_training_result)
        assert result.gate_passed is True
        assert result.metrics["rmse"] <= 1.0

    def test_gate_fail_poor_result(
        self, poor_training_result: TrainingResult
    ) -> None:
        result = evaluate_phase_b(poor_training_result)
        assert result.gate_passed is False

    def test_has_adjacent_accuracy(
        self, good_training_result: TrainingResult
    ) -> None:
        result = evaluate_phase_b(good_training_result)
        assert "adjacent_accuracy" in result.metrics
        assert 0.0 <= result.metrics["adjacent_accuracy"] <= 1.0

    def test_has_per_fold_metrics(
        self, good_training_result: TrainingResult
    ) -> None:
        result = evaluate_phase_b(good_training_result)
        for fold_idx in range(5):
            assert f"fold_{fold_idx}_rmse" in result.metrics


class TestConfusionMatrix:
    def test_correct_shape(self) -> None:
        y_true = np.array([0, 1, 2, 3, 4])
        y_pred = np.array([0.1, 1.2, 1.8, 3.1, 3.9])
        cm = compute_confusion_matrix(y_true, y_pred)
        assert cm.shape == (5, 5)

    def test_perfect_predictions(self) -> None:
        y_true = np.array([0, 1, 2, 3, 4])
        y_pred = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        cm = compute_confusion_matrix(y_true, y_pred)
        assert np.trace(cm) == 5  # All on diagonal

    def test_sums_to_n(self) -> None:
        y_true = np.array([0, 1, 2, 3, 4, 0, 1])
        y_pred = np.array([0.1, 2.1, 1.8, 3.1, 3.9, 1.1, 0.9])
        cm = compute_confusion_matrix(y_true, y_pred)
        assert cm.sum() == 7


class TestOrdinalMetrics:
    def test_perfect_adjacent_accuracy(self) -> None:
        y_true = np.array([0, 1, 2, 3, 4])
        y_pred = np.array([0.4, 1.6, 2.3, 2.8, 3.7])
        metrics = compute_ordinal_metrics(y_true, y_pred)
        assert metrics["adjacent_accuracy"] == 1.0

    def test_has_per_grade_sensitivity(self) -> None:
        y_true = np.array([0, 1, 2, 3, 4])
        y_pred = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        metrics = compute_ordinal_metrics(y_true, y_pred)
        for grade in range(5):
            assert f"sensitivity_kl_{grade}" in metrics
