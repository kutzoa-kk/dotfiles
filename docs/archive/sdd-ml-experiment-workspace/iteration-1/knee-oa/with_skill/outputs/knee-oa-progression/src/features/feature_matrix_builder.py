"""Feature matrix builder for knee OA progression prediction.

Combines joint angle time-series features and clinical metadata
into a single feature matrix suitable for model training.
Only includes features marked as inference_available in feature_availability.yaml.
"""

import logging
from pathlib import Path

import polars as pl
import yaml
from omegaconf import DictConfig

from src.data_access import load_data

logger = logging.getLogger(__name__)


def load_feature_schema(schema_path: str | Path) -> dict:
    """Load feature availability schema."""
    with open(schema_path) as f:
        return yaml.safe_load(f)


def build_feature_matrix(
    cfg: DictConfig,
) -> tuple[pl.DataFrame, pl.Series, pl.Series]:
    """Build feature matrix from raw data.

    Returns:
        Tuple of (features_df, target_series, group_series)
        - features_df: Only inference_available columns
        - target_series: KL grade (0-4)
        - group_series: patient_id for GroupKFold splitting
    """
    # 1. Load raw data
    df = load_data(cfg)
    logger.info(f"Loaded {len(df)} rows")

    # 2. Load feature schema
    schema = load_feature_schema(cfg.data.schema_path)
    available = set(schema["features"]["inference_available"])
    unavailable = set(schema["features"]["inference_unavailable"])

    # 3. Validate no leakage
    actual_cols = set(df.columns)
    feature_cols = sorted(actual_cols & available)
    leaked = set(df.columns) & unavailable
    # Remove leaked columns from the feature set (they should not be used)
    if leaked & set(feature_cols):
        raise ValueError(
            f"Feature matrix contains inference_unavailable columns: "
            f"{leaked & set(feature_cols)}"
        )

    if not feature_cols:
        raise ValueError(
            "No inference_available features found in the data. "
            f"Available columns: {sorted(actual_cols)}, "
            f"Expected features: {sorted(available)}"
        )

    logger.info(f"Using {len(feature_cols)} inference_available features")
    logger.info(f"Feature columns: {feature_cols}")

    # 4. Extract components
    target_column = cfg.data.target_column
    subject_id_field = cfg.data.subject_id_field

    features = df.select(feature_cols)
    target = df.get_column(target_column)
    groups = df.get_column(subject_id_field)

    # 5. Validate shapes
    assert len(features) == len(target), (
        f"Feature/target length mismatch: {len(features)} vs {len(target)}"
    )
    assert len(features) == len(groups), (
        f"Feature/groups length mismatch: {len(features)} vs {len(groups)}"
    )

    return features, target, groups
