"""Tests for knee angle feature extractor."""

import numpy as np
import pytest

from src.features.knee_angle_extractor import (
    extract_all_features,
    extract_angular_velocity_features,
    extract_gait_phase_features,
    extract_rom_features,
    extract_variability_features,
)


@pytest.fixture
def normal_gait_cycle() -> np.ndarray:
    """Simulated normal knee flexion/extension during one gait cycle (100 Hz)."""
    t = np.linspace(0, 1.0, 100)  # 1 second at 100 Hz
    # Simplified knee angle: stance phase flexion ~20 deg, swing ~60 deg
    angle = 10 + 15 * np.sin(2 * np.pi * t) + 25 * np.sin(4 * np.pi * t)
    return angle


@pytest.fixture
def severe_oa_gait_cycle() -> np.ndarray:
    """Simulated severe OA gait with reduced ROM."""
    t = np.linspace(0, 1.0, 100)
    # Reduced ROM, higher baseline flexion
    angle = 20 + 8 * np.sin(2 * np.pi * t) + 10 * np.sin(4 * np.pi * t)
    return angle


class TestROMFeatures:
    def test_returns_dict(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_rom_features(normal_gait_cycle)
        assert isinstance(result, dict)

    def test_has_required_keys(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_rom_features(normal_gait_cycle)
        assert "knee_flex_max" in result
        assert "knee_flex_min" in result
        assert "knee_rom" in result

    def test_rom_is_positive(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_rom_features(normal_gait_cycle)
        assert result["knee_rom"] > 0

    def test_rom_greater_for_normal(
        self, normal_gait_cycle: np.ndarray, severe_oa_gait_cycle: np.ndarray
    ) -> None:
        """Normal gait should have greater ROM than severe OA."""
        normal = extract_rom_features(normal_gait_cycle)
        severe = extract_rom_features(severe_oa_gait_cycle)
        assert normal["knee_rom"] > severe["knee_rom"]

    def test_empty_data_returns_nan(self) -> None:
        result = extract_rom_features(np.array([]))
        assert np.isnan(result["knee_rom"])


class TestAngularVelocityFeatures:
    def test_returns_dict(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_angular_velocity_features(normal_gait_cycle)
        assert isinstance(result, dict)

    def test_has_required_keys(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_angular_velocity_features(normal_gait_cycle)
        assert "knee_angular_velocity_max" in result
        assert "knee_angular_velocity_min" in result
        assert "knee_angular_velocity_mean" in result
        assert "knee_angular_velocity_std" in result

    def test_max_velocity_positive(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_angular_velocity_features(normal_gait_cycle)
        assert result["knee_angular_velocity_max"] > 0

    def test_short_data_returns_nan(self) -> None:
        result = extract_angular_velocity_features(np.array([5.0]))
        assert np.isnan(result["knee_angular_velocity_max"])


class TestGaitPhaseFeatures:
    def test_returns_dict(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_gait_phase_features(normal_gait_cycle)
        assert isinstance(result, dict)

    def test_has_required_keys(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_gait_phase_features(normal_gait_cycle)
        assert "knee_angle_at_heel_strike" in result
        assert "knee_angle_at_toe_off" in result
        assert "knee_flex_peak_swing" in result
        assert "knee_flex_peak_stance" in result


class TestVariabilityFeatures:
    def test_returns_dict(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_variability_features(normal_gait_cycle)
        assert isinstance(result, dict)

    def test_std_positive(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_variability_features(normal_gait_cycle)
        assert result["knee_angle_std"] > 0

    def test_iqr_positive(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_variability_features(normal_gait_cycle)
        assert result["knee_angle_iqr"] > 0


class TestExtractAllFeatures:
    def test_returns_all_features(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_all_features(normal_gait_cycle)
        assert len(result) >= 14  # ROM(3) + velocity(4) + phase(4) + variability(3)

    def test_all_values_are_float(self, normal_gait_cycle: np.ndarray) -> None:
        result = extract_all_features(normal_gait_cycle)
        for key, value in result.items():
            assert isinstance(value, float), f"{key} is {type(value)}, expected float"
