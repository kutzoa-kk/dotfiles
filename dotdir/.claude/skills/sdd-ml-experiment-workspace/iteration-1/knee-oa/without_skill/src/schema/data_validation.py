"""Data validation schema using Pandera for Knee OA Progression project.

Run before any data processing:
    python -m src.schema.data_validation --input data/processed/dataset.parquet

Medical compliance: validates ranges against clinical norms.
"""

import argparse
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema


# Clinical metadata schema
metadata_schema = DataFrameSchema(
    columns={
        "patient_id": Column(
            str,
            Check.str_length(min_value=1),
            nullable=False,
            description="Primary subject identifier for split grouping",
        ),
        "sex": Column(
            str,
            Check.isin(["M", "F"]),
            nullable=False,
            description="Biological sex (M/F)",
        ),
        "age": Column(
            float,
            Check.in_range(18, 100),
            nullable=False,
            description="Age at measurement (years)",
        ),
        "side": Column(
            str,
            Check.isin(["L", "R"]),
            nullable=False,
            description="Knee side (L=left, R=right), must be co-located with patient_id",
        ),
        "kl_grade": Column(
            int,
            Check.in_range(0, 4),
            nullable=False,
            description="Kellgren-Lawrence grade (0-4, ordinal target)",
        ),
        "visit_date": Column(
            str,
            nullable=False,
            description="Visit date for temporal holdout split (YYYY-MM-DD format)",
        ),
    },
    coerce=True,
    strict="filter",
)

# Knee angle features schema (representative columns)
knee_angle_schema = DataFrameSchema(
    columns={
        "patient_id": Column(
            str,
            Check.str_length(min_value=1),
            nullable=False,
        ),
        "side": Column(
            str,
            Check.isin(["L", "R"]),
            nullable=False,
        ),
        "knee_flex_max": Column(
            float,
            Check.in_range(0.0, 180.0),
            nullable=True,
            description="Maximum knee flexion angle (degrees)",
        ),
        "knee_rom": Column(
            float,
            Check.in_range(0.0, 180.0),
            nullable=True,
            description="Knee range of motion (degrees)",
        ),
    },
    coerce=True,
    strict="filter",
)


def validate_metadata(filepath: Path) -> pd.DataFrame:
    """Load and validate clinical metadata. Raise on schema violation."""
    df = _load_file(filepath)
    validated = metadata_schema.validate(df, lazy=True)
    print(f"Metadata validation passed: {len(validated)} rows, {len(validated.columns)} columns")
    return validated


def validate_knee_angles(filepath: Path) -> pd.DataFrame:
    """Load and validate knee angle feature data. Raise on schema violation."""
    df = _load_file(filepath)
    validated = knee_angle_schema.validate(df, lazy=True)
    print(f"Knee angle validation passed: {len(validated)} rows, {len(validated.columns)} columns")
    return validated


def validate_kl_grade_distribution(df: pd.DataFrame) -> dict[str, object]:
    """Validate KL grade distribution for medical compliance.

    Medical compliance requires:
    - Minimum 10 samples per KL grade for reliable estimation
    - No single grade dominates >60% of samples (class imbalance check)

    Returns:
        Dict with distribution stats and compliance flags.
    """
    grade_counts = df["kl_grade"].value_counts().sort_index()
    total = len(df)
    min_count = int(grade_counts.min())
    max_ratio = float(grade_counts.max() / total)

    return {
        "grade_distribution": grade_counts.to_dict(),
        "total_samples": total,
        "min_grade_count": min_count,
        "max_grade_ratio": max_ratio,
        "min_samples_met": min_count >= 10,
        "class_balance_met": max_ratio <= 0.60,
    }


def _load_file(filepath: Path) -> pd.DataFrame:
    """Load a data file by extension."""
    suffix = filepath.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(filepath)
    elif suffix == ".csv":
        return pd.read_csv(filepath)
    elif suffix in (".h5", ".hdf5"):
        return pd.read_hdf(filepath)
    else:
        msg = f"Unsupported format: {suffix}"
        raise ValueError(msg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dataset schema")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--type", choices=["metadata", "knee_angles"], default="metadata")
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    if args.type == "metadata":
        validate_metadata(args.input)
    elif args.type == "knee_angles":
        validate_knee_angles(args.input)


if __name__ == "__main__":
    main()
