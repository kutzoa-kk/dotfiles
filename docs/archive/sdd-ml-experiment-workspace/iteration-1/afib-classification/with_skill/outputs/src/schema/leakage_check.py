"""Feature leakage checker for AF classification experiment.

Validates that no inference_unavailable features are used in the training pipeline.
Must be run before every model training run.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def check_feature_leakage(
    feature_columns: list[str],
    schema_path: str | Path = "src/schema/feature_availability.yaml",
) -> list[str]:
    """Check for feature leakage against the availability schema.

    Args:
        feature_columns: List of feature column names being used.
        schema_path: Path to the feature availability schema.

    Returns:
        List of leaked column names (empty if no leakage).

    Raises:
        FileNotFoundError: If schema file does not exist.
    """
    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    unavailable = set(schema["features"]["inference_unavailable"])
    leaked = sorted(set(feature_columns) & unavailable)

    if leaked:
        logger.error(
            f"LEAKAGE DETECTED: {len(leaked)} inference_unavailable "
            f"features found in training data: {leaked}"
        )
    else:
        logger.info("Leakage check passed: no unavailable features detected")

    return leaked


def validate_feature_set(
    feature_columns: list[str],
    schema_path: str | Path = "src/schema/feature_availability.yaml",
) -> dict[str, list[str]]:
    """Validate feature set against availability schema.

    Args:
        feature_columns: List of feature column names being used.
        schema_path: Path to the feature availability schema.

    Returns:
        Dictionary with 'available', 'unavailable', and 'unknown' feature lists.
    """
    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    available_set = set(schema["features"]["inference_available"])
    unavailable_set = set(schema["features"]["inference_unavailable"])
    feature_set = set(feature_columns)

    return {
        "available": sorted(feature_set & available_set),
        "unavailable": sorted(feature_set & unavailable_set),
        "unknown": sorted(feature_set - available_set - unavailable_set),
    }
