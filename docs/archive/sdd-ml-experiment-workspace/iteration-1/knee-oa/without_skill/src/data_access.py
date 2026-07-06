"""Centralized data access layer for Knee OA Progression project.

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.

Data sources:
    Joint angle time-series: HDF5 files at 100 Hz
    Clinical metadata: CSV with patient demographics and KL grades

Join pattern:
    metadata.csv <-> knee_angles.h5 on [patient_id, side, visit_date]
"""

from pathlib import Path

import polars as pl


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# Default data paths
DEFAULT_METADATA_PATH = RAW_DIR / "clinical_metadata.csv"
DEFAULT_ANGLES_DIR = RAW_DIR / "knee_angles"

# Join keys
JOIN_KEYS = ["patient_id", "side", "visit_date"]

# Metadata column mapping: raw -> cleaned
METADATA_COLUMN_MAP: dict[str, str] = {
    "Patient ID": "patient_id",
    "Visit Date": "visit_date",
    "Age": "age",
    "Sex": "sex",
    "Side": "side",
    "KL Grade": "kl_grade",
    "Radiograph Score": "radiograph_score",
    "WOMAC Total": "womac_total",
    "VAS Pain": "pain_score",
    "BMI": "bmi",
}

# Sampling rate for time-series data
SAMPLING_RATE_HZ = 100


def load_metadata(filepath: Path | None = None) -> pl.DataFrame:
    """Load and clean clinical metadata with standardized column names.

    Returns:
        DataFrame with cleaned column names and validated types.
    """
    path = filepath or DEFAULT_METADATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Clinical metadata not found: {path}")

    df = pl.read_csv(path, infer_schema_length=10000)

    # Rename columns using mapping
    existing_renames = {k: v for k, v in METADATA_COLUMN_MAP.items() if k in df.columns}
    df = df.rename(existing_renames)

    # Extract visit year for temporal splitting
    if "visit_date" in df.columns:
        df = df.with_columns(
            pl.col("visit_date")
            .str.slice(0, 4)
            .cast(pl.Int32)
            .alias("visit_year")
        )

    return df


def load_knee_angle_features(filepath: Path | None = None) -> pl.DataFrame:
    """Load extracted knee angle features (pre-computed from HDF5 time-series).

    Features are extracted from 100 Hz joint angle data and include:
    - Range of motion metrics
    - Peak angle features
    - Angular velocity features
    - Gait phase timing features

    Returns:
        DataFrame with knee angle features per patient-side-visit.
    """
    path = filepath or (PROCESSED_DIR / "knee_angle_features.parquet")
    if not path.exists():
        raise FileNotFoundError(f"Knee angle features not found: {path}")

    return pl.read_parquet(path)


def load_gait_cycle_features(filepath: Path | None = None) -> pl.DataFrame:
    """Load gait cycle features derived from time-series.

    Features include cadence, stride length, gait speed, stance/swing ratio,
    step width, and gait variability metrics.

    Returns:
        DataFrame with gait cycle features per patient-side-visit.
    """
    path = filepath or (PROCESSED_DIR / "gait_cycle_features.parquet")
    if not path.exists():
        raise FileNotFoundError(f"Gait cycle features not found: {path}")

    return pl.read_parquet(path)


def load_merged_dataset(
    metadata_path: Path | None = None,
    knee_angle_path: Path | None = None,
    gait_cycle_path: Path | None = None,
) -> pl.DataFrame:
    """Load all data sources and merge into a single DataFrame.

    Join pattern: metadata LEFT JOIN features ON [patient_id, side, visit_date]

    Args:
        metadata_path: Path to clinical metadata CSV.
        knee_angle_path: Path to knee angle features parquet.
        gait_cycle_path: Path to gait cycle features parquet.

    Returns:
        Merged DataFrame with metadata + all features.
    """
    df_meta = load_metadata(metadata_path)
    df_knee = load_knee_angle_features(knee_angle_path)
    df_gait = load_gait_cycle_features(gait_cycle_path)

    # Ensure join key types match
    for key in JOIN_KEYS:
        for df in [df_meta, df_knee, df_gait]:
            if key in df.columns:
                df = df.with_columns(pl.col(key).cast(pl.Utf8))

    # Join knee angle features
    df_merged = df_meta.join(
        df_knee,
        on=JOIN_KEYS,
        how="inner",
        suffix="_knee",
    )

    # Join gait cycle features
    df_merged = df_merged.join(
        df_gait,
        on=JOIN_KEYS,
        how="inner",
        suffix="_gait",
    )

    return df_merged


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
