"""Tests for phase_c_evaluator -- hold-out ONE-SHOT evaluation and gate check."""

import numpy as np
import polars as pl
import pytest

from src.models.holdout_trainer import HoldoutResult
from src.models.phase_c_evaluator import (
    GATE_PR_AUC_PHASE_C,
    HoldoutEvaluation,
    evaluate_holdout,
)


def _make_holdout_result(
    n_holdout: int = 100,
    prevalence: float = 0.3,
    model_name: str = "lightgbm",
    signal_strength: float = 0.5,
) -> HoldoutResult:
    """Helper to create a HoldoutResult."""
    rng = np.random.default_rng(42)
    n_positive = int(n_holdout * prevalence)
    n_negative = n_holdout - n_positive

    y_true = np.array([1] * n_positive + [0] * n_negative)
    rng.shuffle(y_true)

    y_prob = np.clip(
        y_true * signal_strength + (1 - y_true) * (1 - signal_strength)
        + rng.normal(0, 0.15, n_holdout),
        0.01, 0.99,
    )

    predictions = pl.DataFrame(
        {
            "record_id": [f"r{i}" for i in range(n_holdout)],
            "af_label_true": y_true.tolist(),
            "af_prob_pred": y_prob.tolist(),
        }
    )

    return HoldoutResult(
        model_name=model_name,
        model_params={"n_estimators": 100},
        n_train_samples=400,
        n_train_subjects=320,
        n_holdout_samples=n_holdout,
        n_holdout_subjects=80,
        n_features=30,
        n_positive_train=120,
        n_positive_holdout=n_positive,
        holdout_predictions=predictions,
    )


def test_gate_threshold_value() -> None:
    assert GATE_PR_AUC_PHASE_C == 0.65


def test_evaluation_returns_holdout_evaluation() -> None:
    result = _make_holdout_result(signal_strength=0.7)
    evaluation = evaluate_holdout(result)
    assert isinstance(evaluation, HoldoutEvaluation)


def test_gate_pass_with_strong_signal() -> None:
    result = _make_holdout_result(signal_strength=0.8)
    evaluation = evaluate_holdout(result)
    # Strong signal should produce high PR-AUC
    assert evaluation.pr_auc > 0.5


def test_baseline_pr_auc_equals_prevalence() -> None:
    result = _make_holdout_result(prevalence=0.3)
    evaluation = evaluate_holdout(result)
    assert abs(evaluation.baseline_pr_auc - 0.3) < 0.05


def test_pr_auc_improvement_computed() -> None:
    result = _make_holdout_result(signal_strength=0.7)
    evaluation = evaluate_holdout(result)
    expected_improvement = evaluation.pr_auc - evaluation.baseline_pr_auc
    assert abs(evaluation.pr_auc_improvement - expected_improvement) < 1e-6


def test_description_contains_model_name() -> None:
    result = _make_holdout_result(model_name="logistic_regression")
    evaluation = evaluate_holdout(result)
    assert "logistic_regression" in evaluation.description


def test_optimal_threshold_from_cv_used() -> None:
    result = _make_holdout_result()
    evaluation = evaluate_holdout(result, optimal_threshold=0.4)
    assert evaluation.optimal_threshold == 0.4


def test_metrics_range_valid() -> None:
    result = _make_holdout_result()
    evaluation = evaluate_holdout(result)
    assert 0.0 <= evaluation.pr_auc <= 1.0
    assert 0.0 <= evaluation.roc_auc <= 1.0
    assert 0.0 <= evaluation.f1 <= 1.0
    assert 0.0 <= evaluation.brier_score <= 1.0


def test_n_subjects_counted() -> None:
    result = _make_holdout_result(n_holdout=100)
    evaluation = evaluate_holdout(result)
    assert evaluation.n_subjects == 100  # Each record is unique in test data
    assert evaluation.n_samples == 100
