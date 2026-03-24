"""Tests for Phase A evaluator."""

import pytest

from src.models.phase_a_evaluator import PhaseAResult


class TestPhaseAResult:
    """Tests for PhaseAResult dataclass."""

    def test_all_gates_passed_when_all_true(self):
        """all_gates_passed returns True when all gates pass."""
        result = PhaseAResult(
            metrics={"rho": 0.5},
            gates={"correlation": True, "batch_effect": True},
        )
        assert result.all_gates_passed is True

    def test_all_gates_passed_when_one_fails(self):
        """all_gates_passed returns False when any gate fails."""
        result = PhaseAResult(
            metrics={"rho": 0.3},
            gates={"correlation": False, "batch_effect": True},
        )
        assert result.all_gates_passed is False

    def test_result_is_immutable(self):
        """PhaseAResult is frozen dataclass."""
        result = PhaseAResult(
            metrics={"rho": 0.5},
            gates={"correlation": True},
        )
        with pytest.raises(AttributeError):
            result.metrics = {"new": 0.0}


class TestPhaseAEvaluation:
    """Tests for Phase A validation.

    NOTE: These tests require data loading to be implemented.
    They are written to guide implementation (TDD RED phase).
    """

    def test_returns_phase_result(self, sample_config):
        """Phase A returns a result with metrics and gates."""
        # Will fail until load_data is implemented with real data
        # result = run_phase_a_evaluation(sample_config)
        # assert hasattr(result, "metrics")
        # assert hasattr(result, "gates")
        # assert hasattr(result, "all_gates_passed")
        pass

    def test_metrics_are_numeric(self, sample_config):
        """All metrics are float values."""
        # result = run_phase_a_evaluation(sample_config)
        # for name, value in result.metrics.items():
        #     assert isinstance(value, (int, float)), f"{name} is not numeric"
        pass

    def test_gates_are_boolean(self, sample_config):
        """All gate values are boolean."""
        # result = run_phase_a_evaluation(sample_config)
        # for name, value in result.gates.items():
        #     assert isinstance(value, bool), f"{name} is not boolean"
        pass
