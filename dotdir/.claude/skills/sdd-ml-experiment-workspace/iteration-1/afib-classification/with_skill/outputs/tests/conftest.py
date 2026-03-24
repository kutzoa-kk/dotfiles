"""Shared test fixtures for afib-classification.

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
def sample_ecg_data() -> pl.DataFrame:
    """Minimal synthetic ECG feature dataset for testing.

    Contains enough rows and variety to exercise data processing logic
    without being so large that tests are slow.
    """
    np.random.seed(42)
    n = 50

    return pl.DataFrame({
        "record_id": [f"rec_{i:03d}" for i in range(n)],
        "rr_mean": np.random.uniform(600, 1200, n).tolist(),
        "rr_std": np.random.uniform(10, 200, n).tolist(),
        "rr_median": np.random.uniform(600, 1200, n).tolist(),
        "rr_iqr": np.random.uniform(20, 300, n).tolist(),
        "rr_rmssd": np.random.uniform(10, 150, n).tolist(),
        "rr_pnn50": np.random.uniform(0, 100, n).tolist(),
        "p_wave_duration": np.random.uniform(80, 120, n).tolist(),
        "p_wave_amplitude": np.random.uniform(0.05, 0.3, n).tolist(),
        "p_wave_area": np.random.uniform(5, 30, n).tolist(),
        "p_wave_morphology_score": np.random.uniform(0, 1, n).tolist(),
        "qrs_duration": np.random.uniform(80, 120, n).tolist(),
        "qrs_amplitude": np.random.uniform(0.5, 2.0, n).tolist(),
        "qrs_area": np.random.uniform(20, 100, n).tolist(),
        "hrv_sdnn": np.random.uniform(20, 200, n).tolist(),
        "hrv_sdsd": np.random.uniform(10, 150, n).tolist(),
        "hrv_lf_power": np.random.uniform(100, 5000, n).tolist(),
        "hrv_hf_power": np.random.uniform(50, 3000, n).tolist(),
        "hrv_lf_hf_ratio": np.random.uniform(0.5, 5.0, n).tolist(),
        "hrv_sample_entropy": np.random.uniform(0, 2.5, n).tolist(),
        "hrv_approximate_entropy": np.random.uniform(0, 2.0, n).tolist(),
        "heart_rate_mean": np.random.uniform(50, 150, n).tolist(),
        "heart_rate_std": np.random.uniform(2, 30, n).tolist(),
        "heart_rate_min": np.random.uniform(40, 80, n).tolist(),
        "heart_rate_max": np.random.uniform(80, 200, n).tolist(),
        "af_label": np.random.choice([0, 1], n, p=[0.7, 0.3]).tolist(),
    })


@pytest.fixture
def sample_config(tmp_path, sample_ecg_data) -> DictConfig:
    """Minimal Hydra-compatible config for testing.

    Writes synthetic data to temp files and returns config pointing to them.
    """
    # Write synthetic data
    ecg_path = tmp_path / "ecg_features.parquet"
    labels_path = tmp_path / "clinical_labels.csv"

    ecg_cols = [c for c in sample_ecg_data.columns if c not in ("af_label",)]
    sample_ecg_data.select(ecg_cols).write_parquet(ecg_path)

    sample_ecg_data.select(["record_id", "af_label"]).write_csv(labels_path)

    # Write feature schema
    schema_path = tmp_path / "feature_availability.yaml"
    schema = {
        "features": {
            "inference_available": [
                "rr_mean", "rr_std", "rr_median", "rr_iqr",
                "rr_rmssd", "rr_pnn50",
                "p_wave_duration", "p_wave_amplitude", "p_wave_area",
                "p_wave_morphology_score",
                "qrs_duration", "qrs_amplitude", "qrs_area",
                "hrv_sdnn", "hrv_sdsd", "hrv_lf_power", "hrv_hf_power",
                "hrv_lf_hf_ratio", "hrv_sample_entropy",
                "hrv_approximate_entropy",
                "heart_rate_mean", "heart_rate_std",
                "heart_rate_min", "heart_rate_max",
            ],
            "inference_unavailable": [
                "record_id", "diagnosis_date", "af_label",
                "cardiologist_notes",
            ],
            "auxiliary_targets": [],
        }
    }
    with open(schema_path, "w") as f:
        yaml.dump(schema, f)

    return OmegaConf.create({
        "project_name": "test_afib",
        "experiment_name": "afib-classification",
        "seed": 42,
        "data": {
            "raw_dir": str(tmp_path),
            "processed_dir": str(tmp_path / "processed"),
            "schema_path": str(schema_path),
            "ecg_features_path": str(ecg_path),
            "clinical_labels_path": str(labels_path),
            "join_key": "record_id",
            "target_column": "af_label",
            "subject_id_field": "record_id",
        },
        "model": {
            "name": "lightgbm",
            "type": "lightgbm",
            "params": {
                "n_estimators": 10,
                "learning_rate": 0.1,
                "max_depth": 3,
                "num_leaves": 8,
                "min_child_samples": 5,
                "random_state": 42,
                "verbose": -1,
                "objective": "binary",
            },
        },
        "split": {
            "method": "StratifiedGroupKFold",
            "n_splits": 3,
            "group_key": "record_id",
            "stratify_by": "af_label",
        },
        "gates": {
            "phase_b": {
                "pr_auc": 0.70,
            },
            "phase_c": {
                "pr_auc": 0.65,
            },
        },
        "holdout": {
            "method": "random",
            "test_size": 0.20,
            "random_state": 42,
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
                "rr_mean", "rr_std", "rr_median", "rr_iqr",
                "rr_rmssd", "rr_pnn50",
                "p_wave_duration", "p_wave_amplitude", "p_wave_area",
                "p_wave_morphology_score",
                "qrs_duration", "qrs_amplitude", "qrs_area",
                "hrv_sdnn", "hrv_sdsd", "hrv_lf_power", "hrv_hf_power",
                "hrv_lf_hf_ratio", "hrv_sample_entropy",
                "hrv_approximate_entropy",
                "heart_rate_mean", "heart_rate_std",
                "heart_rate_min", "heart_rate_max",
            ],
            "inference_unavailable": [
                "record_id", "diagnosis_date", "af_label",
                "cardiologist_notes",
            ],
            "auxiliary_targets": [],
        }
    }


@pytest.fixture
def feature_schema_path(tmp_output_dir, feature_schema) -> Path:
    """Write feature schema to temp file and return path."""
    path = tmp_output_dir / "feature_availability.yaml"
    with open(path, "w") as f:
        yaml.dump(feature_schema, f)
    return path
