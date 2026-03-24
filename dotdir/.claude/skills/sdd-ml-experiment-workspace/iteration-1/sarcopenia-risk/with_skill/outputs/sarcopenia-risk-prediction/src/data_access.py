"""Centralized data access layer (Polars).

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.
"""

from pathlib import Path

import polars as pl
from omegaconf import DictConfig


def load_data(cfg: DictConfig) -> pl.DataFrame:
    """Load and join InBody + gait feature data.

    Args:
        cfg: Hydra config with data.inbody_path, data.gait_features_path,
             and data.subject_id.

    Returns:
        Joined DataFrame with InBody labels and gait features,
        joined on the subject ID column (username).
    """
    inbody = load_raw_csv(cfg.data.inbody_path)
    gait = load_raw_parquet(cfg.data.gait_features_path)

    subject_id = cfg.data.subject_id
    joined = inbody.join(gait, on=subject_id, how="inner")

    return joined


def load_raw_csv(filepath: str) -> pl.DataFrame:
    """Load a single raw CSV file. Read-only access."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")
    return pl.read_csv(path)


def load_raw_parquet(filepath: str) -> pl.DataFrame:
    """Load a single raw Parquet file. Read-only access."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found: {path}")
    return pl.read_parquet(path)


def load_raw(filename: str, raw_dir: str = "data/raw") -> pl.DataFrame:
    """Load a single raw data file by name. Read-only access."""
    filepath = Path(raw_dir) / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Raw data not found: {filepath}")

    suffix = filepath.suffix.lower()
    loaders = {
        ".parquet": pl.read_parquet,
        ".csv": pl.read_csv,
        ".feather": pl.read_ipc,
    }
    loader = loaders.get(suffix)
    if loader is None:
        raise ValueError(f"Unsupported format: {suffix}")
    return loader(filepath)


def save_processed(
    df: pl.DataFrame, filename: str, processed_dir: str = "data/processed"
) -> Path:
    """Save processed data to data/processed/."""
    filepath = Path(processed_dir) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(filepath)
    return filepath
