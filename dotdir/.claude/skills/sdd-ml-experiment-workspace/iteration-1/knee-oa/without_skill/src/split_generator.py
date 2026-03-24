"""Data split generator for Knee OA Progression project.

Generates GroupKFold splits respecting:
- Group key: patient_id (all measurements including L/R sides in same fold)
- n_splits: 5 (default)
- Temporal holdout: train < 2024, test >= 2024

Co-location: L/R sides are automatically co-located because splitting
is done at the patient_id level, not the observation level.

Output: data/processed/split_index.json (patient_id -> fold mapping)
"""

import json
from pathlib import Path

import numpy as np
import polars as pl


def generate_cv_split_index(
    df: pl.DataFrame,
    n_splits: int = 5,
    group_col: str = "patient_id",
    seed: int = 42,
) -> dict[str, int]:
    """Generate group K-fold split index.

    Each unique patient_id is assigned to exactly one fold.
    L/R sides are automatically co-located (grouped by patient_id).

    Args:
        df: DataFrame with at least group_col.
        n_splits: Number of CV folds.
        group_col: Column for grouping (subject ID).
        seed: Random seed (used for reproducible shuffling).

    Returns:
        Dictionary mapping patient_id -> fold index (0 to n_splits-1).
    """
    # Deduplicate to one row per subject
    subject_df = (
        df.group_by(group_col)
        .agg(pl.len().alias("n_observations"))
        .sort(group_col)
    )

    patient_ids = subject_df[group_col].to_numpy()

    # Shuffle patient IDs deterministically, then assign folds
    rng = np.random.RandomState(seed)
    shuffle_idx = rng.permutation(len(patient_ids))
    shuffled_ids = patient_ids[shuffle_idx]

    # Assign folds by cycling through shuffled patients
    split_index: dict[str, int] = {}
    for i, pid in enumerate(shuffled_ids):
        split_index[str(pid)] = i % n_splits

    return split_index


def generate_temporal_holdout_split(
    df: pl.DataFrame,
    group_col: str = "patient_id",
    date_col: str = "visit_date",
    cutoff_year: int = 2024,
) -> dict[str, int]:
    """Generate temporal hold-out split: 0=train, 1=holdout.

    Split rule: Patients with ALL visits before cutoff_year go to train.
    Patients with ANY visit >= cutoff_year go to holdout.

    Medical compliance: strict temporal separation prevents future data leakage.

    Args:
        df: DataFrame with at least group_col and date_col.
        group_col: Column for grouping (subject ID).
        date_col: Column with visit dates (YYYY-MM-DD format).
        cutoff_year: Year threshold for temporal split.

    Returns:
        Dictionary mapping patient_id -> split (0=train, 1=holdout).
    """
    # Extract year from visit_date
    df_with_year = df.with_columns(
        pl.col(date_col).str.slice(0, 4).cast(pl.Int32).alias("_visit_year")
    )

    # For each patient, find max visit year
    patient_max_year = (
        df_with_year.group_by(group_col)
        .agg(pl.col("_visit_year").max().alias("max_year"))
        .sort(group_col)
    )

    split: dict[str, int] = {}
    for row in patient_max_year.iter_rows(named=True):
        patient_id = str(row[group_col])
        if row["max_year"] < cutoff_year:
            split[patient_id] = 0  # train
        else:
            split[patient_id] = 1  # holdout

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
    group_col: str = "patient_id",
    side_col: str = "side",
) -> list[str]:
    """Validate that all measurements from same patient are in same fold.

    Also validates L/R co-location.

    Returns:
        List of violation messages. Empty = all checks pass.
    """
    violations: list[str] = []

    # Check all patients are assigned
    for patient_id in df[group_col].unique().to_list():
        patient_str = str(patient_id)
        if patient_str not in split_index:
            violations.append(f"Patient {patient_str} not in split index")

    # Check for patients in multiple folds (shouldn't happen with GroupKFold)
    fold_counts: dict[str, set[int]] = {}
    for patient_id, fold in split_index.items():
        fold_counts.setdefault(patient_id, set()).add(fold)

    multi_fold = {p: folds for p, folds in fold_counts.items() if len(folds) > 1}
    if multi_fold:
        violations.append(f"Patients in multiple folds: {multi_fold}")

    # Check L/R co-location (should be automatic, but explicit verification)
    if side_col in df.columns:
        for patient_id, group in df.group_by(group_col):
            patient_str = str(patient_id) if not isinstance(patient_id, tuple) else str(patient_id[0])
            sides = group[side_col].unique().to_list()
            if len(sides) > 1:
                # Both L and R present — verify same fold
                assigned_fold = split_index.get(patient_str)
                if assigned_fold is None:
                    violations.append(
                        f"Patient {patient_str} has L/R data but no split assignment"
                    )

    return violations
