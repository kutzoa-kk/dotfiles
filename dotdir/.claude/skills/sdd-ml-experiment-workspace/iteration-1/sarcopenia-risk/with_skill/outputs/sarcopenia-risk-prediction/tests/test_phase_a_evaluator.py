"""Tests for Phase A evaluator."""

import pytest

from src.models.phase_a_evaluator import PhaseAResult, run_phase_a_evaluation


class TestPhaseAResult:
    """Tests for PhaseAResult dataclass."""

    def test_all_gates_passed_when_all_true(self):
        """all_gates_passed returns True when all gates pass."""
        result = PhaseAResult(
            metrics={"rho": 0.6},
            gates={"rho": True},
        )
        assert result.all_gates_passed is True

    def test_all_gates_passed_when_any_false(self):
        """all_gates_passed returns False when any gate fails."""
        result = PhaseAResult(
            metrics={"rho": 0.3, "var": 0.1},
            gates={"rho": False, "var": True},
        )
        assert result.all_gates_passed is False

    def test_immutable(self):
        """PhaseAResult is frozen (immutable)."""
        result = PhaseAResult(metrics={}, gates={})
        with pytest.raises(AttributeError):
            result.metrics = {"new": 1.0}


class TestPhaseAEvaluation:
    """Tests for Phase A validation.

    These tests require sample data files to be available.
    They guide the implementation of the score validation logic.
    """

    def test_returns_phase_result(
        self, sample_config, sample_data_files, feature_schema_path
    ):
        """Phase A returns a result with metrics and gates."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )

        result = run_phase_a_evaluation(sample_config)
        assert hasattr(result, "metrics")
        assert hasattr(result, "gates")
        assert hasattr(result, "all_gates_passed")

    def test_metrics_are_numeric(
        self, sample_config, sample_data_files, feature_schema_path
    ):
        """All metrics are float values."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )

        result = run_phase_a_evaluation(sample_config)
        for name, value in result.metrics.items():
            assert isinstance(value, (int, float)), f"{name} is not numeric"

    def test_gates_are_boolean(
        self, sample_config, sample_data_files, feature_schema_path
    ):
        """All gate values are boolean."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )

        result = run_phase_a_evaluation(sample_config)
        for name, value in result.gates.items():
            assert isinstance(value, bool), f"{name} is not boolean"
