"""Centralized data access layer for AFib Classification project.

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.

Data join pattern:
    ecg_features.parquet <-> clinical_labels.csv  on [record_id]
"""

from pathlib import Path

import polars as pl


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# Join key
JOIN_KEY = "record_id"


def load_ecg_features(filepath: Path | None = None) -> pl.DataFrame:
    """Load ECG feature data from Parquet.

    Returns:
        DataFrame with ECG-derived features and record_id.
    """
    path = filepath or (RAW_DIR / "ecg_features.parquet")
    if not path.exists():
        raise FileNotFoundError(f"ECG features not found: {path}")

    return pl.read_parquet(path)


def load_clinical_labels(filepath: Path | None = None) -> pl.DataFrame:
    """Load clinical label data from CSV.

    Returns:
        DataFrame with af_label and clinical metadata.
    """
    path = filepath or (RAW_DIR / "clinical_labels.csv")
    if not path.exists():
        raise FileNotFoundError(f"Clinical labels not found: {path}")

    return pl.read_csv(path, infer_schema_length=10000)


def load_ecg_with_labels(
    ecg_path: Path | None = None,
    labels_path: Path | None = None,
) -> pl.DataFrame:
    """Load ECG features joined with clinical labels on record_id.

    Args:
        ecg_path: Path to ECG features Parquet.
        labels_path: Path to clinical labels CSV.

    Returns:
        Joined DataFrame with ECG features and AF labels.
    """
    df_ecg = load_ecg_features(ecg_path)
    df_labels = load_clinical_labels(labels_path)

    # Ensure join key types match
    df_ecg = df_ecg.with_columns(pl.col(JOIN_KEY).cast(pl.Utf8))
    df_labels = df_labels.with_columns(pl.col(JOIN_KEY).cast(pl.Utf8))

    # Inner join: only keep rows with both ECG features and labels
    df_joined = df_labels.join(
        df_ecg,
        on=JOIN_KEY,
        how="inner",
        suffix="_ecg",
    )

    return df_joined


def save_processed(df: pl.DataFrame, filename: str, fmt: str = "parquet") -> Path:
    """Save processed data to data/processed/."""
    filepath = PROCESSED_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "parquet":
        df.write_parquet(filepath)
    elif fmt == "csv":
        df.write_csv(filepath)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return filepath
