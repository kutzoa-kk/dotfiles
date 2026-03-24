"""Centralized data access layer (Polars).

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.

Data sources:
    - Joint angle time-series: HDF5 at 100 Hz
    - Clinical metadata: CSV with KL grade and demographics
"""

from pathlib import Path

import polars as pl
from omegaconf import DictConfig


def load_joint_angles(cfg: DictConfig) -> pl.DataFrame:
    """Load joint angle time-series from HDF5.

    Args:
        cfg: Hydra config with data.joint_angles_path.

    Returns:
        DataFrame with patient_id, side, and time-series features.
    """
    filepath = Path(cfg.data.joint_angles_path)
    if not filepath.exists():
        raise FileNotFoundError(f"Joint angles file not found: {filepath}")

    # HDF5 loading requires h5py; convert to Polars DataFrame
    import h5py
    import numpy as np

    records = []
    with h5py.File(filepath, "r") as f:
        for patient_id in f.keys():
            patient_group = f[patient_id]
            for side in patient_group.keys():
                side_group = patient_group[side]
                record = {
                    "patient_id": patient_id,
                    "side": side,
                }
                # Extract time-series arrays and compute summary features
                for key in side_group.keys():
                    data = np.array(side_group[key])
                    record[f"{key}_mean"] = float(np.mean(data))
                    record[f"{key}_std"] = float(np.std(data))
                    record[f"{key}_max"] = float(np.max(data))
                    record[f"{key}_min"] = float(np.min(data))
                    record[f"{key}_range"] = float(np.ptp(data))
                records.append(record)

    return pl.DataFrame(records)


def load_clinical_metadata(cfg: DictConfig) -> pl.DataFrame:
    """Load clinical metadata CSV.

    Args:
        cfg: Hydra config with data.clinical_metadata_path.

    Returns:
        DataFrame with patient_id, side, kl_grade, demographics.
    """
    filepath = Path(cfg.data.clinical_metadata_path)
    if not filepath.exists():
        raise FileNotFoundError(f"Clinical metadata not found: {filepath}")

    return pl.read_csv(filepath)


def load_data(cfg: DictConfig) -> pl.DataFrame:
    """Load and join all data sources.

    Joins joint angle features with clinical metadata on (patient_id, side).

    Args:
        cfg: Hydra config with data paths and join keys.

    Returns:
        Joined DataFrame with features and target (kl_grade).
    """
    angles_df = load_joint_angles(cfg)
    clinical_df = load_clinical_metadata(cfg)

    join_keys = list(cfg.data.join_keys)
    joined = angles_df.join(clinical_df, on=join_keys, how="inner")

    if len(joined) == 0:
        raise ValueError(
            f"Join on {join_keys} produced 0 rows. "
            "Check that patient_id and side match between data sources."
        )

    return joined


def load_raw(filename: str, raw_dir: str = "data/raw") -> pl.DataFrame:
    """Load a single raw data file. Read-only access."""
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
