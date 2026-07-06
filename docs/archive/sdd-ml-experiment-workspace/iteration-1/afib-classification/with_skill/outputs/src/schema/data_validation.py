"""Data validation for AF classification experiment.

Validates data integrity before any processing or model training.
Must be run before every pipeline execution.
"""

import logging
from dataclasses import dataclass

import polars as pl

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """Immutable validation result."""

    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


REQUIRED_COLUMNS = [
    "record_id",
    "af_label",
]

EXPECTED_ECG_FEATURES = [
    "rr_mean",
    "rr_std",
    "rr_median",
    "rr_iqr",
    "rr_rmssd",
    "rr_pnn50",
    "p_wave_duration",
    "p_wave_amplitude",
    "p_wave_area",
    "p_wave_morphology_score",
    "qrs_duration",
    "qrs_amplitude",
    "qrs_area",
    "hrv_sdnn",
    "hrv_sdsd",
    "hrv_lf_power",
    "hrv_hf_power",
    "hrv_lf_hf_ratio",
    "hrv_sample_entropy",
    "hrv_approximate_entropy",
    "heart_rate_mean",
    "heart_rate_std",
    "heart_rate_min",
    "heart_rate_max",
]


def validate_data(df: pl.DataFrame) -> ValidationResult:
    """Validate the joined dataset for AF classification.

    Checks:
    - Required columns present
    - af_label is binary (0 or 1)
    - No duplicate record_ids
    - Feature columns are numeric
    - Missing value rates

    Args:
        df: Joined DataFrame to validate.

    Returns:
        ValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check required columns
    actual_cols = set(df.columns)
    for col in REQUIRED_COLUMNS:
        if col not in actual_cols:
            errors.append(f"Missing required column: {col}")

    if errors:
        return ValidationResult(
            is_valid=False, errors=tuple(errors), warnings=tuple(warnings)
        )

    # Check af_label is binary
    unique_labels = df.get_column("af_label").unique().to_list()
    if not set(unique_labels).issubset({0, 1}):
        errors.append(
            f"af_label must be binary (0 or 1), found: {unique_labels}"
        )

    # Check for duplicate record_ids
    n_records = df.select("record_id").n_unique()
    if n_records < len(df):
        warnings.append(
            f"Duplicate record_ids detected: {len(df)} rows, "
            f"{n_records} unique records"
        )

    # Check feature columns are numeric
    for col in EXPECTED_ECG_FEATURES:
        if col in actual_cols:
            dtype = df.get_column(col).dtype
            if dtype not in (pl.Float32, pl.Float64, pl.Int32, pl.Int64):
                errors.append(f"Feature '{col}' is not numeric: {dtype}")

    # Check missing values
    for col in EXPECTED_ECG_FEATURES:
        if col in actual_cols:
            null_rate = df.get_column(col).null_count() / len(df)
            if null_rate > 0.5:
                warnings.append(
                    f"Feature '{col}' has >50% missing values: {null_rate:.1%}"
                )
            elif null_rate > 0.0:
                logger.info(f"Feature '{col}' missing rate: {null_rate:.1%}")

    # Check class balance
    af_rate = df.get_column("af_label").mean()
    if af_rate < 0.01 or af_rate > 0.99:
        warnings.append(
            f"Extreme class imbalance: AF rate = {af_rate:.3f}. "
            "Consider using class weighting or oversampling."
        )

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid, errors=tuple(errors), warnings=tuple(warnings)
    )
