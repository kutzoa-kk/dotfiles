"""Shared test fixtures for sarcopenia-risk-prediction.

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
    """
    np.random.seed(42)
    n = 50

    data = {
        "username": [f"subj_{i:03d}" for i in range(n)],
        "gender": np.random.choice([0, 1], size=n).tolist(),
        "sarcopenia_risk_score": np.random.randn(n).tolist(),
        # Simulated unavailable columns (for leakage testing)
        "age": np.random.randint(40, 90, size=n).tolist(),
        "height": np.random.uniform(150, 185, size=n).tolist(),
        "weight": np.random.uniform(45, 100, size=n).tolist(),
        "bmi": np.random.uniform(18, 35, size=n).tolist(),
        "smi": np.random.uniform(4, 12, size=n).tolist(),
    }

    # Add simulated walk features
    for i in range(10):
        data[f"walk_feature_{i:03d}"] = np.random.randn(n).tolist()

    # Add simulated step features
    for i in range(5):
        data[f"step_feature_{i:03d}"] = np.random.randn(n).tolist()

    return pl.DataFrame(data)


@pytest.fixture
def sample_config(tmp_output_dir) -> DictConfig:
    """Minimal Hydra-compatible config for testing.

    Mirrors the structure of conf/config.yaml but with test-appropriate values.
    """
    schema_path = tmp_output_dir / "feature_availability.yaml"

    return OmegaConf.create(
        {
            "project_name": "test_experiment",
            "experiment_name": "sarcopenia-risk-prediction",
            "seed": 42,
            "data": {
                "raw_dir": str(tmp_output_dir / "raw"),
                "processed_dir": str(tmp_output_dir / "processed"),
                "schema_path": str(schema_path),
                "inbody_path": str(tmp_output_dir / "raw" / "inbody.csv"),
                "gait_features_path": str(
                    tmp_output_dir / "raw" / "gait_features.parquet"
                ),
                "subject_id": "username",
                "target_column": "sarcopenia_risk_score",
            },
            "model": {
                "name": "baseline",
                "type": "lightgbm",
                "params": {
                    "n_estimators": 10,
                    "learning_rate": 0.1,
                    "max_depth": 3,
                    "num_leaves": 8,
                    "min_child_samples": 2,
                    "random_state": 42,
                    "verbose": -1,
                },
            },
            "split": {
                "method": "GroupKFold",
                "n_splits": 3,
                "group_key": "username",
            },
            "gates": {
                "phase_a": {
                    "min_spearman_rho": 0.5,
                },
                "phase_b": {
                    "min_spearman_rho": 0.3,
                },
                "phase_c": {
                    "min_spearman_rho": 0.0,
                },
            },
            "holdout": {
                "method": "random",
                "test_ratio": 0.2,
                "random_state": 42,
            },
        }
    )


@pytest.fixture
def tmp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def feature_schema() -> dict:
    """Feature availability schema for testing."""
    walk_features = [f"walk_feature_{i:03d}" for i in range(10)]
    step_features = [f"step_feature_{i:03d}" for i in range(5)]

    return {
        "features": {
            "inference_available": ["gender"] + walk_features + step_features,
            "inference_unavailable": [
                "uuid",
                "username",
                "test_date_time",
                "height",
                "weight",
                "age",
                "bmi",
                "smi",
                "vfl",
                "sarcopenia_risk_score",
            ],
            "auxiliary_targets": [],
        },
        "metadata": {
            "subject_id": "username",
            "target": "sarcopenia_risk_score",
            "task_type": "regression",
        },
    }


@pytest.fixture
def feature_schema_path(tmp_output_dir, feature_schema) -> Path:
    """Write feature schema to temp file and return path."""
    path = tmp_output_dir / "feature_availability.yaml"
    with open(path, "w") as f:
        yaml.dump(feature_schema, f)
    return path


@pytest.fixture
def sample_data_files(tmp_output_dir, sample_data):
    """Create sample CSV and Parquet files in a temp directory."""
    raw_dir = tmp_output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Split sample_data into InBody (labels) and gait (features)
    inbody_cols = [
        "username",
        "gender",
        "sarcopenia_risk_score",
        "age",
        "height",
        "weight",
        "bmi",
        "smi",
    ]
    gait_cols = ["username"] + [
        c for c in sample_data.columns if c not in inbody_cols
    ]

    inbody_df = sample_data.select(inbody_cols)
    gait_df = sample_data.select(gait_cols)

    inbody_path = raw_dir / "inbody.csv"
    gait_path = raw_dir / "gait_features.parquet"

    inbody_df.write_csv(inbody_path)
    gait_df.write_parquet(gait_path)

    return {"inbody_path": inbody_path, "gait_path": gait_path}
