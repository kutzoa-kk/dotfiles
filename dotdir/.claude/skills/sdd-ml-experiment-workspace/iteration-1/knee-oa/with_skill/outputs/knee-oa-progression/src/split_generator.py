"""Split generator with integrity validation.

Creates CV and holdout splits respecting patient_id grouping.
Left/right knee (side) data for the same patient is always co-located.
"""

import json
import logging
from pathlib import Path

import numpy as np
import polars as pl
from omegaconf import DictConfig
from sklearn.model_selection import GroupKFold

logger = logging.getLogger(__name__)


def generate_splits(
    cfg: DictConfig, groups: np.ndarray
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate CV splits respecting group constraints.

    Both left and right knees of the same patient are always in the same fold,
    because GroupKFold groups by patient_id.

    Args:
        cfg: Config with split.method, split.n_splits, split.group_key.
        groups: Array of group labels (patient_id values).

    Returns:
        List of (train_indices, val_indices) tuples.
    """
    n_splits = cfg.split.n_splits

    match cfg.split.method:
        case "GroupKFold":
            splitter = GroupKFold(n_splits=n_splits)
            X_dummy = np.zeros(len(groups))
            splits = list(splitter.split(X_dummy, groups=groups))
            _validate_no_group_leakage(groups, splits)
            return splits
        case _:
            raise ValueError(f"Unknown split method: {cfg.split.method}")


def generate_temporal_holdout(
    df: pl.DataFrame, cfg: DictConfig
) -> tuple[np.ndarray, np.ndarray]:
    """Generate temporal holdout split.

    Train: visit_date < cutoff_date
    Test:  visit_date >= cutoff_date

    All data for a patient is placed entirely in train or test based on
    their most recent visit date to avoid temporal leakage.

    Args:
        df: DataFrame with visit_date column.
        cfg: Config with holdout.cutoff_date.

    Returns:
        Tuple of (train_indices, test_indices).
    """
    cutoff = cfg.holdout.cutoff_date

    # Assign based on visit_date
    train_mask = df["visit_date"].cast(pl.Utf8) < cutoff
    test_mask = ~train_mask

    train_indices = np.where(train_mask.to_numpy())[0]
    test_indices = np.where(test_mask.to_numpy())[0]

    if len(test_indices) == 0:
        raise ValueError(f"No test samples after cutoff date {cutoff}")
    if len(train_indices) == 0:
        raise ValueError(f"No training samples before cutoff date {cutoff}")

    logger.info(
        f"Temporal holdout: {len(train_indices)} train, "
        f"{len(test_indices)} test (cutoff={cutoff})"
    )

    return train_indices, test_indices


def _validate_no_group_leakage(
    groups: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
) -> None:
    """Validate that no group appears in both train and validation of any fold."""
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        train_groups = set(groups[train_idx])
        val_groups = set(groups[val_idx])
        overlap = train_groups & val_groups
        if overlap:
            raise ValueError(
                f"Group leakage in fold {fold_idx}: "
                f"{len(overlap)} groups appear in both train and val: {overlap}"
            )


def save_split_index(
    groups: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
    output_path: str = "data/processed/split_index.json",
) -> Path:
    """Save split assignment as audit artifact."""
    index = {}
    for fold_idx, (_, val_idx) in enumerate(splits):
        for idx in val_idx:
            group_key = str(groups[idx])
            if group_key not in index:
                index[group_key] = fold_idx

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(index, f, indent=2)

    logger.info(f"Split index saved to {path}")
    return path
