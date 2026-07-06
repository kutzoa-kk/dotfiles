"""Feature matrix builder for sarcopenia risk prediction.

Combines InBody and gait feature data into a single feature matrix
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
    """Load feature availability schema."""
    with open(schema_path) as f:
        return yaml.safe_load(f)


def get_available_feature_columns(
    schema: dict, actual_columns: list[str]
) -> list[str]:
    """Determine which columns are inference-available.

    Args:
        schema: Feature availability schema dict.
        actual_columns: Actual column names in the DataFrame.

    Returns:
        Sorted list of inference-available column names.
    """
    unavailable = set(schema["features"]["inference_unavailable"])
    available_explicit = set(schema["features"].get("inference_available", []))

    # If explicit list provided, use intersection with actual columns
    if available_explicit:
        return sorted(set(actual_columns) & available_explicit)

    # Otherwise, use all columns except unavailable ones
    return sorted(set(actual_columns) - unavailable)


def build_feature_matrix(
    cfg: DictConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build feature matrix from raw data.

    Returns:
        Tuple of (features_array, target_array, groups_array)
        - features_array: Only inference_available columns (numpy)
        - target_array: The sarcopenia risk score (numpy)
        - groups_array: Subject IDs (username) for GroupKFold splitting (numpy)
    """
    # 1. Load raw data
    df = load_data(cfg)
    logger.info(f"Loaded {len(df)} rows")

    # 2. Load feature schema
    schema = load_feature_schema(cfg.data.schema_path)
    unavailable = set(schema["features"]["inference_unavailable"])

    # 3. Validate no leakage
    actual_cols = set(df.columns)
    feature_cols = get_available_feature_columns(schema, df.columns)
    leaked = set(feature_cols) & unavailable
    if leaked:
        raise ValueError(
            f"Feature matrix contains inference_unavailable columns: {leaked}"
        )

    logger.info(f"Using {len(feature_cols)} inference_available features")

    # 4. Extract components
    target_col = cfg.data.target_column
    group_col = cfg.data.subject_id

    features = df.select(feature_cols).to_numpy()
    target = df.get_column(target_col).to_numpy()
    groups = df.get_column(group_col).to_numpy()

    return features, target, groups
