"""Leakage detection module.

Validates that no inference-unavailable features appear in the
training feature set. Must be run before every training run.
"""

import logging
from pathlib import Path

import yaml
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


def check_feature_leakage(
    cfg: DictConfig,
    feature_columns: list[str] | None = None,
) -> None:
    """Check for feature leakage against the schema.

    Args:
        cfg: Hydra config with data.schema_path.
        feature_columns: Optional explicit list of feature columns to check.
            If None, loads from the schema and logs a warning.

    Raises:
        ValueError: If any inference_unavailable feature is detected.
    """
    schema_path = Path(cfg.data.schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Feature schema not found: {schema_path}")

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    unavailable = set(schema["features"]["inference_unavailable"])

    if feature_columns is None:
        logger.info(
            "No explicit feature list provided — "
            "leakage check will run at build_feature_matrix time."
        )
        return

    leaked = set(feature_columns) & unavailable
    if leaked:
        raise ValueError(
            f"LEAKAGE DETECTED: The following inference_unavailable "
            f"features were found in the training set: {sorted(leaked)}. "
            f"Remove these features before training."
        )

    logger.info(
        f"Leakage check passed: {len(feature_columns)} features, "
        f"0 leaks detected."
    )


def check_target_not_in_features(
    target_column: str,
    feature_columns: list[str],
) -> None:
    """Verify the target variable is not included as a feature.

    Args:
        target_column: Name of the target variable.
        feature_columns: List of feature column names.

    Raises:
        ValueError: If target column is found in features.
    """
    if target_column in feature_columns:
        raise ValueError(
            f"LEAKAGE DETECTED: Target column '{target_column}' "
            f"found in feature columns. This will cause perfect "
            f"but meaningless predictions."
        )
