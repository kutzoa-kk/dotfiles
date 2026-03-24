"""Shared test fixtures for knee-oa-progression.

Provides synthetic datasets, mock configs, and temporary directories.
All fixtures create minimal but realistic data structures.
"""

import tempfile
from pathlib import Path

import numpy as np
import polars as pl
import pytest
import yaml
from omegaconf import DictConfig, OmegaConf


@pytest.fixture
def sample_data() -> pl.DataFrame:
    """Minimal synthetic dataset for testing.

    Contains enough rows and variety to exercise data processing logic
    without being so large that tests are slow.
    Simulates both left and right knees for each patient.
    """
    np.random.seed(42)
    n_patients = 25
    records = []

    for i in range(n_patients):
        for side in ["L", "R"]:
            kl_grade = np.random.randint(0, 5)
            records.append({
                "patient_id": f"PAT_{i:03d}",
                "side": side,
                "kl_grade": kl_grade,
                "radiograph_score": float(kl_grade) + np.random.normal(0, 0.3),
                "age": int(np.random.uniform(40, 80)),
                "sex": np.random.choice(["M", "F"]),
                "bmi": float(np.random.uniform(20, 35)),
                "visit_date": f"202{np.random.choice([2, 3, 4])}-{np.random.randint(1, 13):02d}-01",
                # Knee angle features
                "knee_flexion_mean": float(np.random.uniform(10, 60) + kl_grade * 2),
                "knee_flexion_std": float(np.random.uniform(2, 10)),
                "knee_flexion_range": float(np.random.uniform(30, 90)),
                "knee_flexion_max": float(np.random.uniform(50, 100)),
                "knee_flexion_min": float(np.random.uniform(-5, 15)),
                "knee_extension_mean": float(np.random.uniform(-5, 10)),
                "knee_extension_std": float(np.random.uniform(1, 5)),
                "knee_varus_valgus_mean": float(np.random.uniform(-10, 10) + kl_grade * 1.5),
                "knee_varus_valgus_std": float(np.random.uniform(1, 5)),
                "knee_varus_valgus_range": float(np.random.uniform(5, 25)),
                "knee_rotation_mean": float(np.random.uniform(-5, 5)),
                "knee_rotation_std": float(np.random.uniform(1, 4)),
                "knee_rotation_range": float(np.random.uniform(5, 15)),
                # Gait cycle features
                "stance_duration_mean": float(np.random.uniform(0.5, 0.8)),
                "stance_duration_std": float(np.random.uniform(0.02, 0.1)),
                "swing_duration_mean": float(np.random.uniform(0.3, 0.5)),
                "swing_duration_std": float(np.random.uniform(0.01, 0.05)),
                "stride_length_mean": float(np.random.uniform(0.8, 1.5)),
                "stride_length_std": float(np.random.uniform(0.05, 0.2)),
                "cadence_mean": float(np.random.uniform(90, 130)),
                "cadence_std": float(np.random.uniform(2, 10)),
                "gait_speed_mean": float(np.random.uniform(0.8, 1.4) - kl_grade * 0.1),
                "gait_speed_std": float(np.random.uniform(0.05, 0.15)),
                "double_support_time_mean": float(np.random.uniform(0.1, 0.3)),
                "double_support_time_std": float(np.random.uniform(0.01, 0.05)),
            })

    return pl.DataFrame(records)


@pytest.fixture
def sample_config(tmp_output_dir, feature_schema_path) -> DictConfig:
    """Minimal Hydra-compatible config for testing.

    Mirrors the structure of conf/config.yaml but with test-appropriate values.
    """
    return OmegaConf.create({
        "project_name": "test_experiment",
        "experiment_name": "knee-oa-progression-test",
        "seed": 42,
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": str(tmp_output_dir / "processed"),
            "schema_path": str(feature_schema_path),
            "joint_angles_path": "data/raw/joint_angles.h5",
            "clinical_metadata_path": "data/raw/clinical_metadata.csv",
            "join_keys": ["patient_id", "side"],
            "sampling_rate_hz": 100,
            "target_column": "kl_grade",
            "subject_id_field": "patient_id",
            "side_column": "side",
        },
        "model": {
            "name": "baseline",
            "type": "lightgbm",
            "params": {
                "objective": "regression",
                "metric": "rmse",
                "n_estimators": 10,
                "learning_rate": 0.1,
                "max_depth": 3,
                "num_leaves": 8,
                "min_child_samples": 5,
                "random_state": 42,
                "verbose": -1,
            },
        },
        "split": {
            "method": "GroupKFold",
            "n_splits": 3,
            "group_key": "patient_id",
        },
        "gates": {
            "phase_a": {
                "min_spearman_rho": 0.4,
            },
            "phase_b": {
                "max_rmse": 1.0,
            },
            "phase_c": {
                "max_rmse": 1.2,
            },
        },
        "holdout": {
            "method": "temporal",
            "cutoff_date": "2024-01-01",
        },
    })


@pytest.fixture
def tmp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def feature_schema() -> dict:
    """Feature availability schema for testing."""
    return {
        "features": {
            "inference_available": [
                "knee_flexion_mean",
                "knee_flexion_std",
                "knee_flexion_range",
                "knee_flexion_max",
                "knee_flexion_min",
                "knee_extension_mean",
                "knee_extension_std",
                "knee_varus_valgus_mean",
                "knee_varus_valgus_std",
                "knee_varus_valgus_range",
                "knee_rotation_mean",
                "knee_rotation_std",
                "knee_rotation_range",
                "stance_duration_mean",
                "stance_duration_std",
                "swing_duration_mean",
                "swing_duration_std",
                "stride_length_mean",
                "stride_length_std",
                "cadence_mean",
                "cadence_std",
                "gait_speed_mean",
                "gait_speed_std",
                "double_support_time_mean",
                "double_support_time_std",
                "age",
                "sex",
                "bmi",
            ],
            "inference_unavailable": [
                "patient_id",
                "visit_date",
                "kl_grade",
                "radiograph_score",
                "side",
            ],
            "auxiliary_targets": [],
        },
    }


@pytest.fixture
def feature_schema_path(tmp_output_dir, feature_schema) -> Path:
    """Write feature schema to temp file and return path."""
    path = tmp_output_dir / "feature_availability.yaml"
    with open(path, "w") as f:
        yaml.dump(feature_schema, f)
    return path
