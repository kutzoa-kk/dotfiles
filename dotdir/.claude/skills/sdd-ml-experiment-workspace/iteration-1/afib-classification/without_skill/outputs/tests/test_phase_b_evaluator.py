"""Tests for phase_b_evaluator -- OOF prediction evaluation and gate check."""

import numpy as np
import polars as pl
import pytest

from src.models.cv_trainer import CVTrainingResult, FoldResult
from src.models.phase_b_evaluator import GATE_PR_AUC_PHASE_B, PhaseBEvaluation, evaluate_phase_b


def _make_cv_result(
    pooled_pr_auc: float,
    model_name: str = "lightgbm",
    n_samples: int = 200,
    prevalence: float = 0.3,
) -> CVTrainingResult:
    """Helper to create a CVTrainingResult with controlled PR-AUC."""
    rng = np.random.default_rng(42)
    n_positive = int(n_samples * prevalence)
    n_negative = n_samples - n_positive

    y_true = np.array([1] * n_positive + [0] * n_negative)
    # Create predictions that correlate with true labels
    y_prob = np.clip(
        y_true * 0.7 + (1 - y_true) * 0.2 + rng.normal(0, 0.15, n_samples),
        0.01, 0.99,
    )

    rng.shuffle(y_true)
    # Re-correlate
    y_prob = np.clip(
        y_true * 0.7 + (1 - y_true) * 0.2 + rng.normal(0, 0.15, n_samples),
        0.01, 0.99,
    )

    oof = pl.DataFrame(
        {
            "record_id": [f"r{i % 40}" for i in range(n_samples)],
            "af_label_true": y_true.tolist(),
            "af_prob_pred": y_prob.tolist(),
        }
    )

    fold_results = [
        FoldResult(
            fold=i,
            pr_auc=pooled_pr_auc + rng.normal(0, 0.02),
            roc_auc=pooled_pr_auc + rng.normal(0, 0.02),
            n_train=n_samples - n_samples // 5,
            n_test=n_samples // 5,
            n_positive_train=int(n_positive * 0.8),
            n_positive_test=int(n_positive * 0.2),
        )
        for i in range(5)
    ]

    from sklearn.metrics import average_precision_score, roc_auc_score
    actual_pr_auc = float(average_precision_score(y_true, y_prob))
    actual_roc_auc = float(roc_auc_score(y_true, y_prob))

    return CVTrainingResult(
        model_name=model_name,
        fold_results=fold_results,
        oof_predictions=oof,
        pooled_pr_auc=pooled_pr_auc,
        pooled_roc_auc=actual_roc_auc,
    )


def test_gate_pass_when_pr_auc_above_threshold() -> None:
    result = _make_cv_result(pooled_pr_auc=0.80)
    report = evaluate_phase_b(result)
    assert report.gate_passed is True


def test_gate_fail_when_pr_auc_below_threshold() -> None:
    result = _make_cv_result(pooled_pr_auc=0.50)
    report = evaluate_phase_b(result)
    assert report.gate_passed is False


def test_gate_threshold_value() -> None:
    assert GATE_PR_AUC_PHASE_B == 0.70


def test_metrics_contain_required_keys() -> None:
    result = _make_cv_result(pooled_pr_auc=0.75)
    report = evaluate_phase_b(result)
    for key in ["pr_auc", "roc_auc", "f1", "precision", "recall", "brier_score"]:
        assert key in report.metrics, f"Missing metric: {key}"


def test_metrics_contain_per_fold_pr_auc() -> None:
    result = _make_cv_result(pooled_pr_auc=0.75)
    report = evaluate_phase_b(result)
    for i in range(5):
        assert f"fold_{i}_pr_auc" in report.metrics


def test_model_name_preserved() -> None:
    result = _make_cv_result(pooled_pr_auc=0.75, model_name="logistic_regression")
    report = evaluate_phase_b(result)
    assert report.model_name == "logistic_regression"


def test_report_is_phase_b_evaluation() -> None:
    result = _make_cv_result(pooled_pr_auc=0.75)
    report = evaluate_phase_b(result)
    assert isinstance(report, PhaseBEvaluation)


def test_prevalence_computed() -> None:
    result = _make_cv_result(pooled_pr_auc=0.75, prevalence=0.3)
    report = evaluate_phase_b(result)
    assert "prevalence" in report.metrics
    assert 0.0 < report.metrics["prevalence"] < 1.0


def test_description_contains_gate_result() -> None:
    result = _make_cv_result(pooled_pr_auc=0.80)
    report = evaluate_phase_b(result)
    assert "PASS" in report.description or "FAIL" in report.description
