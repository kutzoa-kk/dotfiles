"""Tests for Phase C evaluator."""

import pytest

from src.models.phase_c_evaluator import run_phase_c_evaluation, PhaseCResult


class TestPhaseCEvaluation:
    """Tests for Phase C holdout evaluation."""

    def test_returns_phase_c_result(self, sample_config):
        """Phase C returns a PhaseCResult instance."""
        result = run_phase_c_evaluation(sample_config)
        assert isinstance(result, PhaseCResult)

    def test_result_has_metrics(self, sample_config):
        """Result contains classification metrics."""
        result = run_phase_c_evaluation(sample_config)
        assert "pr_auc" in result.metrics
        assert "roc_auc" in result.metrics
        assert "f1" in result.metrics

    def test_result_has_gates(self, sample_config):
        """Result contains gate evaluations."""
        result = run_phase_c_evaluation(sample_config)
        assert "pr_auc" in result.gates
        assert isinstance(result.gates["pr_auc"], bool)

    def test_all_gates_passed_is_boolean(self, sample_config):
        """all_gates_passed property returns boolean."""
        result = run_phase_c_evaluation(sample_config)
        assert isinstance(result.all_gates_passed, bool)

    def test_metrics_are_in_valid_range(self, sample_config):
        """All metrics are between 0 and 1."""
        result = run_phase_c_evaluation(sample_config)
        for name, value in result.metrics.items():
            assert 0.0 <= value <= 1.0, f"{name}={value} out of range"

    def test_holdout_run_count(self, sample_config):
        """Holdout run count is 1 (one-shot protocol)."""
        result = run_phase_c_evaluation(sample_config)
        assert result.holdout_run_count == 1

    def test_result_has_details(self, sample_config):
        """Result contains holdout split details."""
        result = run_phase_c_evaluation(sample_config)
        assert "train_size" in result.details
        assert "test_size" in result.details
