"""Tests for Phase B evaluator."""

import pytest

from src.models.phase_b_evaluator import run_phase_b_evaluation, PhaseBResult


class TestPhaseBEvaluation:
    """Tests for Phase B cross-validated classification."""

    def test_returns_phase_b_result(self, sample_config):
        """Phase B returns a PhaseBResult instance."""
        result = run_phase_b_evaluation(sample_config)
        assert isinstance(result, PhaseBResult)

    def test_result_has_fold_results(self, sample_config):
        """Result contains per-fold results."""
        result = run_phase_b_evaluation(sample_config)
        assert len(result.fold_results) == sample_config.split.n_splits

    def test_result_has_aggregate_metrics(self, sample_config):
        """Result contains aggregated metrics."""
        result = run_phase_b_evaluation(sample_config)
        assert "pr_auc_mean" in result.aggregate_metrics
        assert "pr_auc_std" in result.aggregate_metrics

    def test_result_has_gates(self, sample_config):
        """Result contains gate evaluations."""
        result = run_phase_b_evaluation(sample_config)
        assert "pr_auc" in result.gates
        assert isinstance(result.gates["pr_auc"], bool)

    def test_all_gates_passed_is_boolean(self, sample_config):
        """all_gates_passed property returns boolean."""
        result = run_phase_b_evaluation(sample_config)
        assert isinstance(result.all_gates_passed, bool)

    def test_oof_predictions_have_correct_length(self, sample_config):
        """OOF predictions cover all samples."""
        result = run_phase_b_evaluation(sample_config)
        assert result.oof_predictions is not None
        # OOF predictions should cover all training samples
        assert len(result.oof_predictions) == 50  # sample size

    def test_fold_metrics_are_numeric(self, sample_config):
        """All per-fold metrics are numeric."""
        result = run_phase_b_evaluation(sample_config)
        for fold_result in result.fold_results:
            for name, value in fold_result.metrics.items():
                assert isinstance(value, (int, float)), f"{name} is not numeric"
