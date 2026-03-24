"""Leakage check for knee OA progression experiment.

Validates that no inference_unavailable features are used in training.
Must be run before every training run.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def check_feature_leakage(
    feature_columns: list[str],
    schema_path: str | Path,
) -> tuple[bool, list[str]]:
    """Check if any leaked features are present in the feature set.

    Args:
        feature_columns: List of column names used in the feature matrix.
        schema_path: Path to feature_availability.yaml.

    Returns:
        Tuple of (is_clean, leaked_columns).
        is_clean is True if no leakage detected.
    """
    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    unavailable = set(schema["features"]["inference_unavailable"])
    feature_set = set(feature_columns)

    leaked = sorted(feature_set & unavailable)

    if leaked:
        logger.error(
            f"LEAKAGE DETECTED: {len(leaked)} inference_unavailable "
            f"features in training data: {leaked}"
        )
        return False, leaked

    logger.info(
        f"Leakage check PASSED: {len(feature_columns)} features verified clean"
    )
    return True, []


def validate_split_integrity(
    train_groups: set[str],
    val_groups: set[str],
) -> tuple[bool, set[str]]:
    """Validate no group overlap between train and validation sets.

    Args:
        train_groups: Set of patient_id values in training set.
        val_groups: Set of patient_id values in validation set.

    Returns:
        Tuple of (is_clean, overlapping_groups).
    """
    overlap = train_groups & val_groups

    if overlap:
        logger.error(
            f"SPLIT LEAKAGE: {len(overlap)} patients appear in both "
            f"train and val: {sorted(overlap)[:10]}..."
        )
        return False, overlap

    logger.info("Split integrity check PASSED: no group overlap")
    return True, set()
