"""Data split generator for AFib Classification project.

Generates StratifiedGroupKFold splits respecting:
- Group key: record_id (all records from same subject in same fold)
- Stratification: af_label (maintain AF prevalence across folds)
- n_splits: 5 (default)

Output: data/processed/split_index.json (record_id -> fold mapping)
"""

import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.model_selection import StratifiedGroupKFold, StratifiedShuffleSplit


def generate_split_index(
    df: pl.DataFrame,
    n_splits: int = 5,
    group_col: str = "record_id",
    stratify_col: str = "af_label",
    seed: int = 42,
) -> dict[str, int]:
    """Generate group-stratified K-fold split index.

    Each unique record_id is assigned to exactly one fold.
    AF prevalence is maintained across folds.

    Args:
        df: DataFrame with at least group_col and stratify_col.
        n_splits: Number of CV folds.
        group_col: Column for grouping (subject ID).
        stratify_col: Column for stratification.
        seed: Random seed.

    Returns:
        Dictionary mapping record_id -> fold index (0 to n_splits-1).
    """
    # Deduplicate to one row per subject
    subject_df = (
        df.group_by(group_col)
        .agg(pl.col(stratify_col).first())
        .sort(group_col)
    )

    record_ids = subject_df[group_col].to_numpy()
    stratify_labels = subject_df[stratify_col].to_numpy()

    # StratifiedGroupKFold needs X, y, groups
    dummy_x = np.zeros(len(record_ids))
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    split_index: dict[str, int] = {}
    for fold_idx, (_train_idx, test_idx) in enumerate(
        sgkf.split(dummy_x, stratify_labels, groups=record_ids)
    ):
        for idx in test_idx:
            split_index[str(record_ids[idx])] = fold_idx

    return split_index


def generate_holdout_split(
    df: pl.DataFrame,
    test_size: float = 0.2,
    group_col: str = "record_id",
    stratify_col: str = "af_label",
    seed: int = 123,
) -> dict[str, int]:
    """Generate hold-out split: 0=train, 1=holdout.

    Splits at the record_id level with AF label stratification.

    Args:
        df: DataFrame with at least group_col and stratify_col.
        test_size: Fraction of subjects for hold-out set.
        group_col: Column for grouping (subject ID).
        stratify_col: Column for stratification.
        seed: Random seed.

    Returns:
        Dictionary mapping record_id -> split (0=train, 1=holdout).
    """
    subject_df = (
        df.group_by(group_col)
        .agg(pl.col(stratify_col).first())
        .sort(group_col)
    )

    record_ids = subject_df[group_col].to_numpy()
    stratify_labels = subject_df[stratify_col].to_numpy()

    sss = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(sss.split(np.zeros(len(record_ids)), stratify_labels))

    split: dict[str, int] = {}
    for idx in train_idx:
        split[str(record_ids[idx])] = 0
    for idx in test_idx:
        split[str(record_ids[idx])] = 1

    return split


def save_split_index(split_index: dict[str, int], output_path: Path) -> Path:
    """Save split index to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(split_index, f, indent=2, ensure_ascii=False)
    return output_path


def validate_split_integrity(
    df: pl.DataFrame,
    split_index: dict[str, int],
    group_col: str = "record_id",
) -> list[str]:
    """Validate that all records from same subject are in same fold.

    Returns:
        List of violation messages. Empty = all checks pass.
    """
    violations: list[str] = []

    for record_id in df[group_col].unique().to_list():
        record_id_str = str(record_id)
        if record_id_str not in split_index:
            violations.append(f"Subject {record_id_str} not in split index")

    # Check for subjects in multiple folds (shouldn't happen with GroupKFold)
    fold_counts: dict[str, set[int]] = {}
    for record_id, fold in split_index.items():
        fold_counts.setdefault(record_id, set()).add(fold)

    multi_fold = {u: folds for u, folds in fold_counts.items() if len(folds) > 1}
    if multi_fold:
        violations.append(f"Subjects in multiple folds: {multi_fold}")

    return violations
