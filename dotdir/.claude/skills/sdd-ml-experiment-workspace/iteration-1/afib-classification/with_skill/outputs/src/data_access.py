"""Centralized data access layer (Polars).

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.
"""

from pathlib import Path

import polars as pl
from omegaconf import DictConfig


def load_data(cfg: DictConfig) -> pl.DataFrame:
    """Load and join ECG features with clinical labels.

    Args:
        cfg: Hydra config with data paths and join keys.

    Returns:
        Joined DataFrame with ECG features and AF labels.
    """
    ecg_features = load_raw(cfg.data.ecg_features_path)
    clinical_labels = load_raw(cfg.data.clinical_labels_path)

    joined = ecg_features.join(
        clinical_labels.select([cfg.data.join_key, cfg.data.target_column]),
        on=cfg.data.join_key,
        how="inner",
    )

    if joined.is_empty():
        raise ValueError(
            f"Join on '{cfg.data.join_key}' produced empty DataFrame. "
            "Check that ECG features and clinical labels share record IDs."
        )

    return joined


def load_raw(filepath: str) -> pl.DataFrame:
    """Load a single raw data file. Read-only access.

    Args:
        filepath: Path to the raw data file.

    Returns:
        DataFrame loaded from file.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is unsupported.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")

    suffix = path.suffix.lower()
    loaders: dict[str, callable] = {
        ".parquet": pl.read_parquet,
        ".csv": pl.read_csv,
        ".feather": pl.read_ipc,
    }
    loader = loaders.get(suffix)
    if loader is None:
        raise ValueError(f"Unsupported format: {suffix}")
    return loader(path)


def save_processed(
    df: pl.DataFrame, filename: str, processed_dir: str = "data/processed"
) -> Path:
    """Save processed data to data/processed/.

    Args:
        df: DataFrame to save.
        filename: Output filename.
        processed_dir: Directory for processed files.

    Returns:
        Path to saved file.
    """
    filepath = Path(processed_dir) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(filepath)
    return filepath
