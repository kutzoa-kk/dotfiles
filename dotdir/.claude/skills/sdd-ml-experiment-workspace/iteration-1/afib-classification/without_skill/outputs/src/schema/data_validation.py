"""Data validation schema using Pandera for AFib Classification.

Run before any data processing:
    python -m src.schema.data_validation --input data/processed/dataset.parquet
"""

import argparse
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema


ecg_dataset_schema = DataFrameSchema(
    columns={
        "record_id": Column(
            str,
            Check.str_length(min_value=1),
            nullable=False,
            description="Primary subject identifier for split grouping",
        ),
        "af_label": Column(
            int,
            Check.isin([0, 1]),
            nullable=False,
            description="Atrial fibrillation label (0=no AF, 1=AF)",
        ),
        "rr_mean": Column(
            float,
            Check.in_range(200, 2000),
            nullable=True,
            description="Mean RR interval (ms)",
        ),
        "rr_std": Column(
            float,
            Check.greater_than_or_equal_to(0),
            nullable=True,
            description="Standard deviation of RR intervals (ms)",
        ),
        "rr_rmssd": Column(
            float,
            Check.greater_than_or_equal_to(0),
            nullable=True,
            description="Root mean square of successive RR differences (ms)",
        ),
        "heart_rate_mean": Column(
            float,
            Check.in_range(20, 300),
            nullable=True,
            description="Mean heart rate (bpm)",
        ),
    },
    coerce=True,
    strict="filter",
)


def validate(filepath: Path) -> pd.DataFrame:
    """Load and validate a dataset file. Raise on schema violation."""
    suffix = filepath.suffix.lower()
    if suffix == ".parquet":
        df = pd.read_parquet(filepath)
    elif suffix == ".csv":
        df = pd.read_csv(filepath)
    else:
        msg = f"Unsupported format: {suffix}"
        raise ValueError(msg)

    validated = ecg_dataset_schema.validate(df, lazy=True)
    print(f"Validation passed: {len(validated)} rows, {len(validated.columns)} columns")
    return validated


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ECG dataset schema")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")
    validate(args.input)


if __name__ == "__main__":
    main()
