"""Data validation module.

Validates raw data before processing to catch schema drift,
missing columns, and data quality issues early.
"""

import logging
from pathlib import Path

import polars as pl
import yaml
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


def validate_data(cfg: DictConfig) -> list[str]:
    """Validate raw data against expected schema.

    Args:
        cfg: Hydra config with data paths and schema_path.

    Returns:
        List of validation error messages (empty if all valid).

    Raises:
        ValueError: If critical validation failures are detected.
    """
    errors: list[str] = []

    # Load schema
    schema_path = Path(cfg.data.schema_path)
    if not schema_path.exists():
        errors.append(f"Feature schema not found: {schema_path}")
        return errors

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    # Check data files exist
    inbody_path = Path(cfg.data.inbody_path)
    if not inbody_path.exists():
        errors.append(f"InBody data not found: {inbody_path}")

    gait_path = Path(cfg.data.gait_features_path)
    if not gait_path.exists():
        errors.append(f"Gait features not found: {gait_path}")

    if errors:
        for err in errors:
            logger.error(f"Validation error: {err}")
        raise ValueError(
            f"Data validation failed with {len(errors)} error(s): {errors}"
        )

    # Load data and validate
    inbody = pl.read_csv(inbody_path)
    gait = pl.read_parquet(gait_path)

    # Check subject ID column exists
    subject_id = cfg.data.subject_id
    if subject_id not in inbody.columns:
        errors.append(f"Subject ID '{subject_id}' not found in InBody data")
    if subject_id not in gait.columns:
        errors.append(f"Subject ID '{subject_id}' not found in gait data")

    # Check for unavailable features not accidentally included
    unavailable = set(schema["features"]["inference_unavailable"])
    for col in unavailable:
        if col in inbody.columns:
            logger.info(f"InBody contains unavailable column (expected): {col}")

    # Check minimum sample count
    if len(inbody) < 10:
        errors.append(f"InBody data has only {len(inbody)} rows (minimum: 10)")
    if len(gait) < 10:
        errors.append(f"Gait data has only {len(gait)} rows (minimum: 10)")

    # Check for duplicate subjects
    if subject_id in inbody.columns:
        n_unique = inbody.get_column(subject_id).n_unique()
        if n_unique < len(inbody):
            logger.warning(
                f"InBody has {len(inbody)} rows but only {n_unique} unique subjects"
            )

    if errors:
        for err in errors:
            logger.error(f"Validation error: {err}")
        raise ValueError(
            f"Data validation failed with {len(errors)} error(s): {errors}"
        )

    logger.info("Data validation passed")
    return errors
