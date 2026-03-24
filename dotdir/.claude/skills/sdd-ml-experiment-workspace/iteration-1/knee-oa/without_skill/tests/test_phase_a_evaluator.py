"""Tests for Phase A evaluator -- biomarker correlation verification.

TDD: Write tests FIRST, then implement.
"""

import numpy as np
import polars as pl
import pytest

from src.models.phase_a_evaluator import (
    EvaluationReport,
    check_gate_conditions,
    evaluate_h1_knee_angle_correlation,
    evaluate_h2_gait_cycle_correlation,
    evaluate_kl_grade_distribution,
    evaluate_known_group_validity,
    run_phase_a_evaluation,
)


@pytest.fixture
def oa_data_with_correlation() -> pl.DataFrame:
    """Data where knee angle features correlate with KL grade."""
    n = 50
    np.random.seed(42)
    kl_grades = np.repeat([0, 1, 2, 3, 4], 10)

    # ROM decreases with KL grade (strong negative correlation)
    knee_rom = 130.0 - kl_grades * 10 + np.random.normal(0, 3, n)
    knee_flex_max = 140.0 - kl_grades * 8 + np.random.normal(0, 2, n)
    cadence = 110.0 - kl_grades * 5 + np.random.normal(0, 3, n)
    gait_speed = 1.2 - kl_grades * 0.15 + np.random.normal(0, 0.05, n)

    return pl.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "side": ["L", "R"] * 25,
        "kl_grade": kl_grades.tolist(),
        "knee_rom": knee_rom.tolist(),
        "knee_flex_max": knee_flex_max.tolist(),
        "cadence": cadence.tolist(),
        "gait_speed": gait_speed.tolist(),
        "age": (50.0 + np.random.normal(0, 5, n)).tolist(),
        "sex": (["M"] * 25 + ["F"] * 25),
    })


@pytest.fixture
def oa_data_no_correlation() -> pl.DataFrame:
    """Data where features do NOT correlate with KL grade."""
    n = 50
    np.random.seed(99)
    kl_grades = np.repeat([0, 1, 2, 3, 4], 10)

    # Random values, no correlation with KL
    knee_rom = np.random.normal(120, 10, n)
    cadence = np.random.normal(100, 8, n)

    return pl.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n)],
        "side": ["L", "R"] * 25,
        "kl_grade": kl_grades.tolist(),
        "knee_rom": knee_rom.tolist(),
        "cadence": cadence.tolist(),
    })


class TestH1KneeAngleCorrelation:
    def test_returns_evaluation_report(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_h1_knee_angle_correlation(
            oa_data_with_correlation, ["knee_rom", "knee_flex_max"]
        )
        assert isinstance(result, EvaluationReport)

    def test_gate_pass_with_correlated_data(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_h1_knee_angle_correlation(
            oa_data_with_correlation, ["knee_rom", "knee_flex_max"]
        )
        assert result.gate_passed is True
        assert result.metrics["max_abs_rho"] >= 0.4

    def test_gate_fail_with_uncorrelated_data(
        self, oa_data_no_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_h1_knee_angle_correlation(
            oa_data_no_correlation, ["knee_rom"]
        )
        assert result.gate_passed is False

    def test_reports_per_feature_correlations(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_h1_knee_angle_correlation(
            oa_data_with_correlation, ["knee_rom", "knee_flex_max"]
        )
        assert "rho_knee_rom" in result.metrics
        assert "rho_knee_flex_max" in result.metrics


class TestH2GaitCycleCorrelation:
    def test_returns_evaluation_report(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_h2_gait_cycle_correlation(
            oa_data_with_correlation, ["cadence", "gait_speed"]
        )
        assert isinstance(result, EvaluationReport)

    def test_gate_pass_with_correlated_data(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_h2_gait_cycle_correlation(
            oa_data_with_correlation, ["cadence", "gait_speed"]
        )
        assert result.gate_passed is True


class TestKnownGroupValidity:
    def test_returns_evaluation_report(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_known_group_validity(oa_data_with_correlation)
        assert isinstance(result, EvaluationReport)

    def test_has_group_counts(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_known_group_validity(oa_data_with_correlation)
        assert "n_severe" in result.metrics
        assert "n_normal" in result.metrics

    def test_gate_passed_none(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        """Known-group validity has no gate -- supplementary only."""
        result = evaluate_known_group_validity(oa_data_with_correlation)
        assert result.gate_passed is None


class TestKLGradeDistribution:
    def test_returns_evaluation_report(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_kl_grade_distribution(oa_data_with_correlation)
        assert isinstance(result, EvaluationReport)

    def test_reports_all_grades(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        result = evaluate_kl_grade_distribution(oa_data_with_correlation)
        for grade in range(5):
            assert f"n_kl_{grade}" in result.metrics


class TestRunPhaseAEvaluation:
    def test_returns_four_reports(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        reports = run_phase_a_evaluation(
            oa_data_with_correlation,
            ["knee_rom", "knee_flex_max"],
            ["cadence", "gait_speed"],
        )
        assert len(reports) == 4

    def test_report_hypotheses(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        reports = run_phase_a_evaluation(
            oa_data_with_correlation,
            ["knee_rom", "knee_flex_max"],
            ["cadence", "gait_speed"],
        )
        hypotheses = [r.hypothesis for r in reports]
        assert "H1" in hypotheses
        assert "H2" in hypotheses
        assert "Known-group validity" in hypotheses
        assert "KL grade distribution" in hypotheses


class TestGateConditions:
    def test_gate_passes_when_h1_passes(
        self, oa_data_with_correlation: pl.DataFrame
    ) -> None:
        reports = run_phase_a_evaluation(
            oa_data_with_correlation,
            ["knee_rom", "knee_flex_max"],
            ["cadence", "gait_speed"],
        )
        assert check_gate_conditions(reports) is True

    def test_gate_fails_when_both_fail(
        self, oa_data_no_correlation: pl.DataFrame
    ) -> None:
        reports = run_phase_a_evaluation(
            oa_data_no_correlation,
            ["knee_rom"],
            ["cadence"],
        )
        assert check_gate_conditions(reports) is False
