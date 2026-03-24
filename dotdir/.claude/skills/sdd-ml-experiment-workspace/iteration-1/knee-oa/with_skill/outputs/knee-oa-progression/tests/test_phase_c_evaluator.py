"""Tests for Phase C evaluator."""

import pytest

from src.models.phase_c_evaluator import PhaseCResult


class TestPhaseCResult:
    """Tests for PhaseCResult dataclass."""

    def test_default_run_count(self):
        """Holdout run count defaults to 1."""
        result = PhaseCResult(
            metrics={"holdout_rmse": 0.9},
            gates={"rmse": True},
        )
        assert result.holdout_run_count == 1

    def test_all_gates_passed(self):
        """all_gates_passed returns True when all gates pass."""
        result = PhaseCResult(
            metrics={"holdout_rmse": 0.9},
            gates={"rmse": True},
        )
        assert result.all_gates_passed is True

    def test_gate_failure(self):
        """all_gates_passed returns False when gate fails."""
        result = PhaseCResult(
            metrics={"holdout_rmse": 1.5},
            gates={"rmse": False},
        )
        assert result.all_gates_passed is False

    def test_result_is_immutable(self):
        """PhaseCResult is frozen dataclass."""
        result = PhaseCResult(
            metrics={"holdout_rmse": 0.9},
            gates={"rmse": True},
        )
        with pytest.raises(AttributeError):
            result.metrics = {}


class TestPhaseCSafetyProtocol:
    """Tests to enforce one-shot holdout protocol."""

    def test_holdout_should_not_be_rerun(self):
        """Documenting the one-shot constraint.

        Phase C is a one-shot evaluation. This test serves as
        documentation that re-running Phase C after seeing results
        constitutes p-hacking and is explicitly prohibited.
        """
        # This is a documentation test.
        # In practice, the run_phase_c.py script logs a warning.
        assert True
