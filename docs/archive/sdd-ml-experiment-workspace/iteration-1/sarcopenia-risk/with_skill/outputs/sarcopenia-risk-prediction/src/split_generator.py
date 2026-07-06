"""Split generator with integrity validation.

Creates CV and holdout splits respecting subject grouping.
Subject ID field: username — all data from the same subject
resides in the same fold.
"""

import json
from pathlib import Path

import numpy as np
from omegaconf import DictConfig
from sklearn.model_selection import GroupKFold, train_test_split


def generate_splits(
    cfg: DictConfig, groups: np.ndarray
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate CV splits respecting group constraints.

    Args:
        cfg: Config with split.method, split.n_splits, split.group_key.
        groups: Array of group labels (username values).

    Returns:
        List of (train_indices, val_indices) tuples.
    """
    n_splits = cfg.split.n_splits

    match cfg.split.method:
        case "GroupKFold":
            splitter = GroupKFold(n_splits=n_splits)
            X_dummy = np.zeros(len(groups))
            return list(splitter.split(X_dummy, groups=groups))
        case _:
            raise ValueError(f"Unknown split method: {cfg.split.method}")


def generate_holdout_split(
    groups: np.ndarray,
    test_ratio: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate holdout split at the subject level.

    Splits unique subjects into train/test, then maps back to sample indices.
    Ensures no subject appears in both train and test.

    Args:
        groups: Array of group labels (username values).
        test_ratio: Fraction of subjects for holdout.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (train_indices, test_indices).
    """
    unique_subjects = np.unique(groups)
    train_subjects, test_subjects = train_test_split(
        unique_subjects, test_size=test_ratio, random_state=random_state
    )

    train_subjects_set = set(train_subjects)
    test_subjects_set = set(test_subjects)

    train_idx = np.array([i for i, g in enumerate(groups) if g in train_subjects_set])
    test_idx = np.array([i for i, g in enumerate(groups) if g in test_subjects_set])

    return train_idx, test_idx


def save_split_index(
    groups: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
    output_path: str = "data/processed/split_index.json",
) -> Path:
    """Save split assignment as audit artifact."""
    index = {}
    for fold_idx, (_, val_idx) in enumerate(splits):
        for idx in val_idx:
            index[str(groups[idx])] = fold_idx

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(index, f, indent=2)
    return path
