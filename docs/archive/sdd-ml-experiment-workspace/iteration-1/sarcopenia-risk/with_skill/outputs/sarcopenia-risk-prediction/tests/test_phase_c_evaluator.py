"""Tests for Phase C evaluator."""

import pytest

from src.models.phase_c_evaluator import PhaseCResult


class TestPhaseCResult:
    """Tests for PhaseCResult dataclass."""

    def test_all_gates_passed_when_true(self):
        """all_gates_passed returns True when all gates pass."""
        result = PhaseCResult(
            metrics={"rho": 0.5},
            gates={"rho": True},
        )
        assert result.all_gates_passed is True

    def test_all_gates_passed_when_false(self):
        """all_gates_passed returns False when any gate fails."""
        result = PhaseCResult(
            metrics={"rho": 0.1},
            gates={"rho": False},
        )
        assert result.all_gates_passed is False

    def test_immutable(self):
        """PhaseCResult is frozen (immutable)."""
        result = PhaseCResult(metrics={}, gates={})
        with pytest.raises(AttributeError):
            result.metrics = {"new": 1.0}

    def test_default_holdout_run_count(self):
        """Default holdout run count is 1."""
        result = PhaseCResult(metrics={}, gates={})
        assert result.holdout_run_count == 1
