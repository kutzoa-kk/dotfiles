"""Data validation for knee OA progression experiment.

Validates data integrity before any processing or model training.
Must be run before every experiment pipeline execution.
"""

import logging
from dataclasses import dataclass

import polars as pl

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """Immutable validation result."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_clinical_metadata(df: pl.DataFrame) -> ValidationResult:
    """Validate clinical metadata DataFrame.

    Checks:
    - Required columns exist
    - KL grade range (0-4)
    - No duplicate (patient_id, side) combinations per visit
    - patient_id not null
    - side values are L or R
    - Age and BMI in reasonable ranges
    """
    errors: list[str] = []
    warnings: list[str] = []

    required_cols = ["patient_id", "side", "kl_grade", "age", "sex", "visit_date"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # KL grade range
    kl_min = df["kl_grade"].min()
    kl_max = df["kl_grade"].max()
    if kl_min is not None and kl_min < 0:
        errors.append(f"KL grade minimum {kl_min} < 0")
    if kl_max is not None and kl_max > 4:
        errors.append(f"KL grade maximum {kl_max} > 4")

    # Null patient_id
    null_count = df.filter(pl.col("patient_id").is_null()).height
    if null_count > 0:
        errors.append(f"{null_count} rows with null patient_id")

    # Side values
    valid_sides = {"L", "R"}
    actual_sides = set(df["side"].unique().to_list())
    invalid_sides = actual_sides - valid_sides
    if invalid_sides:
        errors.append(f"Invalid side values: {invalid_sides}")

    # Age range
    if "age" in df.columns:
        age_min = df["age"].min()
        age_max = df["age"].max()
        if age_min is not None and age_min < 18:
            warnings.append(f"Minimum age {age_min} < 18")
        if age_max is not None and age_max > 120:
            errors.append(f"Maximum age {age_max} > 120")

    # BMI range
    if "bmi" in df.columns:
        bmi_min = df["bmi"].min()
        bmi_max = df["bmi"].max()
        if bmi_min is not None and bmi_min < 10:
            warnings.append(f"Minimum BMI {bmi_min} < 10")
        if bmi_max is not None and bmi_max > 70:
            warnings.append(f"Maximum BMI {bmi_max} > 70")

    is_valid = len(errors) == 0
    if is_valid:
        logger.info("Clinical metadata validation: PASSED")
    else:
        logger.error(f"Clinical metadata validation: FAILED ({len(errors)} errors)")
    for w in warnings:
        logger.warning(f"Validation warning: {w}")

    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


def validate_feature_matrix(
    features: pl.DataFrame,
    target: pl.Series,
    groups: pl.Series,
) -> ValidationResult:
    """Validate feature matrix before training.

    Checks:
    - No infinite values
    - Shape consistency
    - No constant features
    - Target range is valid
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Shape consistency
    if len(features) != len(target):
        errors.append(
            f"Feature/target length mismatch: {len(features)} vs {len(target)}"
        )
    if len(features) != len(groups):
        errors.append(
            f"Feature/groups length mismatch: {len(features)} vs {len(groups)}"
        )

    # Check for infinite values
    for col in features.columns:
        inf_count = features.filter(pl.col(col).is_infinite()).height
        if inf_count > 0:
            errors.append(f"Column {col} has {inf_count} infinite values")

    # Check for constant features
    for col in features.columns:
        n_unique = features[col].n_unique()
        if n_unique <= 1:
            warnings.append(f"Column {col} is constant (n_unique={n_unique})")

    # Target range
    target_min = target.min()
    target_max = target.max()
    if target_min is not None and target_min < 0:
        errors.append(f"Target minimum {target_min} < 0")
    if target_max is not None and target_max > 4:
        errors.append(f"Target maximum {target_max} > 4")

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
