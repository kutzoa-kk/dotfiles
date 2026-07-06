"""Feature matrix builder for AF classification.

Combines ECG features and clinical labels into a single feature matrix
suitable for model training. Only includes features marked as
inference_available in feature_availability.yaml.
"""

import logging
from pathlib import Path

import numpy as np
import polars as pl
import yaml
from omegaconf import DictConfig

from src.data_access import load_data

logger = logging.getLogger(__name__)


def load_feature_schema(schema_path: str | Path) -> dict:
    """Load feature availability schema.

    Args:
        schema_path: Path to feature_availability.yaml.

    Returns:
        Parsed YAML schema dictionary.
    """
    with open(schema_path) as f:
        return yaml.safe_load(f)


def build_feature_matrix(
    cfg: DictConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build feature matrix from raw data.

    Loads ECG features and clinical labels, validates against the feature
    availability schema, and returns numpy arrays ready for model training.

    Args:
        cfg: Hydra config with data paths, schema path, and column names.

    Returns:
        Tuple of (X, y, groups) where:
        - X: Feature matrix (n_samples, n_features) as numpy array
        - y: Binary AF labels as numpy array
        - groups: Record IDs for GroupKFold splitting as numpy array

    Raises:
        ValueError: If feature matrix contains inference_unavailable columns.
    """
    # 1. Load raw data
    df = load_data(cfg)
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")

    # 2. Load feature schema
    schema = load_feature_schema(cfg.data.schema_path)
    available = set(schema["features"]["inference_available"])
    unavailable = set(schema["features"]["inference_unavailable"])

    # 3. Validate no leakage
    actual_cols = set(df.columns)
    feature_cols = sorted(actual_cols & available)
    leaked = set(df.columns) & unavailable
    if leaked:
        raise ValueError(
            f"Feature matrix contains inference_unavailable columns: {leaked}"
        )

    logger.info(f"Using {len(feature_cols)} inference_available features")
    logger.info(f"Features: {feature_cols}")

    # 4. Extract components
    features = df.select(feature_cols)
    target = df.get_column(cfg.data.target_column)
    groups = df.get_column(cfg.data.subject_id_field)

    # 5. Log class distribution
    class_counts = target.value_counts()
    logger.info(f"Class distribution:\n{class_counts}")

    return (
        features.to_numpy(),
        target.to_numpy(),
        groups.to_numpy(),
    )
