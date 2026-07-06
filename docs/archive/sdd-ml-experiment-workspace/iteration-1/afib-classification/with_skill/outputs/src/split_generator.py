"""Split generator with integrity validation.

Creates CV and holdout splits respecting record_id grouping
and af_label stratification.
"""

import json
import logging
from pathlib import Path

import numpy as np
from omegaconf import DictConfig
from sklearn.model_selection import (
    GroupKFold,
    StratifiedGroupKFold,
    GroupShuffleSplit,
)

logger = logging.getLogger(__name__)


def generate_cv_splits(
    cfg: DictConfig,
    y: np.ndarray,
    groups: np.ndarray,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate CV splits respecting group constraints and stratification.

    Args:
        cfg: Config with split.method, split.n_splits, split.group_key.
        y: Target array for stratification.
        groups: Array of group labels (record IDs).

    Returns:
        List of (train_indices, val_indices) tuples.

    Raises:
        ValueError: If split method is unknown.
    """
    n_splits = cfg.split.n_splits
    x_dummy = np.zeros(len(groups))

    match cfg.split.method:
        case "StratifiedGroupKFold":
            splitter = StratifiedGroupKFold(
                n_splits=n_splits, shuffle=True, random_state=cfg.seed
            )
            splits = list(splitter.split(x_dummy, y, groups=groups))
        case "GroupKFold":
            splitter = GroupKFold(n_splits=n_splits)
            splits = list(splitter.split(x_dummy, groups=groups))
        case _:
            raise ValueError(f"Unknown split method: {cfg.split.method}")

    _validate_no_group_leakage(groups, splits)
    return splits


def generate_holdout_split(
    cfg: DictConfig,
    groups: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate train/test holdout split respecting group constraints.

    Args:
        cfg: Config with holdout.test_size and holdout.random_state.
        groups: Array of group labels (record IDs).

    Returns:
        Tuple of (train_indices, test_indices).
    """
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=cfg.holdout.test_size,
        random_state=cfg.holdout.random_state,
    )
    x_dummy = np.zeros(len(groups))
    train_idx, test_idx = next(splitter.split(x_dummy, groups=groups))

    _validate_no_group_leakage(groups, [(train_idx, test_idx)])
    logger.info(
        f"Holdout split: train={len(train_idx)}, test={len(test_idx)} "
        f"({len(test_idx) / len(groups) * 100:.1f}% test)"
    )
    return train_idx, test_idx


def _validate_no_group_leakage(
    groups: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
) -> None:
    """Validate that no group appears in both train and validation.

    Args:
        groups: Array of group labels.
        splits: List of (train_idx, val_idx) tuples.

    Raises:
        ValueError: If group leakage is detected.
    """
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        train_groups = set(groups[train_idx])
        val_groups = set(groups[val_idx])
        overlap = train_groups & val_groups
        if overlap:
            raise ValueError(
                f"Group leakage in fold {fold_idx}: "
                f"{len(overlap)} groups appear in both train and validation: "
                f"{list(overlap)[:5]}..."
            )


def save_split_index(
    groups: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
    output_path: str = "data/processed/split_index.json",
) -> Path:
    """Save split assignment as audit artifact.

    Args:
        groups: Array of group labels.
        splits: List of (train_idx, val_idx) tuples.
        output_path: Path for the output JSON file.

    Returns:
        Path to saved file.
    """
    index: dict[str, int] = {}
    for fold_idx, (_, val_idx) in enumerate(splits):
        for idx in val_idx:
            index[str(groups[idx])] = fold_idx

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(index, f, indent=2)
    return path
