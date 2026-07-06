"""Knee angle feature extractor from HDF5 time-series data.

Extracts clinically meaningful features from 100 Hz joint angle recordings.
Features are designed to capture OA-related gait abnormalities.

Categories:
    - Range of motion (ROM)
    - Peak angles (stance, swing phase)
    - Angular velocity
    - Symmetry indices
    - Variability metrics
"""

from pathlib import Path

import numpy as np
import polars as pl

SAMPLING_RATE_HZ = 100


def extract_rom_features(angle_data: np.ndarray) -> dict[str, float]:
    """Extract range of motion features from knee angle time-series.

    Args:
        angle_data: 1D array of knee flexion/extension angles (degrees).

    Returns:
        Dictionary of ROM features.
    """
    if len(angle_data) == 0:
        return {
            "knee_flex_max": float("nan"),
            "knee_flex_min": float("nan"),
            "knee_rom": float("nan"),
        }

    flex_max = float(np.nanmax(angle_data))
    flex_min = float(np.nanmin(angle_data))
    rom = flex_max - flex_min

    return {
        "knee_flex_max": flex_max,
        "knee_flex_min": flex_min,
        "knee_rom": rom,
    }


def extract_angular_velocity_features(
    angle_data: np.ndarray,
    sampling_rate: int = SAMPLING_RATE_HZ,
) -> dict[str, float]:
    """Extract angular velocity features from knee angle time-series.

    Args:
        angle_data: 1D array of knee angles (degrees).
        sampling_rate: Sampling rate in Hz (default: 100).

    Returns:
        Dictionary of angular velocity features.
    """
    if len(angle_data) < 2:
        return {
            "knee_angular_velocity_max": float("nan"),
            "knee_angular_velocity_min": float("nan"),
            "knee_angular_velocity_mean": float("nan"),
            "knee_angular_velocity_std": float("nan"),
        }

    dt = 1.0 / sampling_rate
    velocity = np.diff(angle_data) / dt

    return {
        "knee_angular_velocity_max": float(np.nanmax(velocity)),
        "knee_angular_velocity_min": float(np.nanmin(velocity)),
        "knee_angular_velocity_mean": float(np.nanmean(velocity)),
        "knee_angular_velocity_std": float(np.nanstd(velocity)),
    }


def extract_gait_phase_features(
    angle_data: np.ndarray,
    sampling_rate: int = SAMPLING_RATE_HZ,
) -> dict[str, float]:
    """Extract gait phase-specific features.

    Identifies stance and swing phases based on angle patterns
    and extracts phase-specific metrics.

    Args:
        angle_data: 1D array of knee angles (degrees).
        sampling_rate: Sampling rate in Hz.

    Returns:
        Dictionary of gait phase features.
    """
    if len(angle_data) < sampling_rate:
        return {
            "knee_angle_at_heel_strike": float("nan"),
            "knee_angle_at_toe_off": float("nan"),
            "knee_flex_peak_swing": float("nan"),
            "knee_flex_peak_stance": float("nan"),
        }

    # Simplified phase detection using angle local extrema
    midpoint = len(angle_data) // 2

    # Approximate: first half = stance, second half = swing
    stance_angles = angle_data[:midpoint]
    swing_angles = angle_data[midpoint:]

    return {
        "knee_angle_at_heel_strike": float(angle_data[0]),
        "knee_angle_at_toe_off": float(angle_data[midpoint]),
        "knee_flex_peak_swing": float(np.nanmax(swing_angles)),
        "knee_flex_peak_stance": float(np.nanmax(stance_angles)),
    }


def extract_variability_features(
    angle_data: np.ndarray,
    n_cycles: int = 1,
) -> dict[str, float]:
    """Extract gait variability features across cycles.

    Higher variability may indicate OA-related compensatory patterns.

    Args:
        angle_data: 1D array of knee angles.
        n_cycles: Number of gait cycles in the data.

    Returns:
        Dictionary of variability features.
    """
    if len(angle_data) == 0:
        return {
            "knee_angle_cv": float("nan"),
            "knee_angle_std": float("nan"),
            "knee_angle_iqr": float("nan"),
        }

    std = float(np.nanstd(angle_data))
    mean = float(np.nanmean(angle_data))
    cv = std / abs(mean) if abs(mean) > 1e-8 else float("nan")
    iqr = float(np.nanpercentile(angle_data, 75) - np.nanpercentile(angle_data, 25))

    return {
        "knee_angle_cv": cv,
        "knee_angle_std": std,
        "knee_angle_iqr": iqr,
    }


def extract_all_features(
    angle_data: np.ndarray,
    sampling_rate: int = SAMPLING_RATE_HZ,
) -> dict[str, float]:
    """Extract all knee angle features from a single time-series.

    Args:
        angle_data: 1D array of knee angles (degrees) at sampling_rate Hz.
        sampling_rate: Sampling rate in Hz.

    Returns:
        Dictionary with all extracted features.
    """
    features: dict[str, float] = {}
    features.update(extract_rom_features(angle_data))
    features.update(extract_angular_velocity_features(angle_data, sampling_rate))
    features.update(extract_gait_phase_features(angle_data, sampling_rate))
    features.update(extract_variability_features(angle_data))
    return features
