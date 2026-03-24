"""Feature matrix builder for Knee OA Progression.

Constructs the final feature matrix by:
1. Loading knee angle features and gait cycle features
2. Merging with clinical metadata
3. Filtering to inference_available features only
4. Applying leakage checks

Output: data/processed/feature_matrix.parquet
"""

from pathlib import Path

import polars as pl
import yaml


def load_feature_schema(schema_path: Path) -> dict[str, list[str]]:
    """Load feature availability schema.

    Returns:
        Dict with keys: inference_available, inference_unavailable, auxiliary_targets.
    """
    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    features = schema.get("features", {})
    return {
        "inference_available": features.get("inference_available", []),
        "inference_unavailable": features.get("inference_unavailable", []),
        "auxiliary_targets": features.get("auxiliary_targets", []),
    }


def build_feature_matrix(
    df: pl.DataFrame,
    schema_path: Path,
    target_col: str = "kl_grade",
    group_col: str = "patient_id",
    side_col: str = "side",
) -> tuple[pl.DataFrame, list[str]]:
    """Build feature matrix, excluding forbidden columns.

    Retains: group_col, side_col, target_col + inference_available features.
    Removes: inference_unavailable + auxiliary_targets (except target_col itself).

    Args:
        df: Merged DataFrame with all columns.
        schema_path: Path to feature_availability.yaml.
        target_col: Name of the target column.
        group_col: Name of the subject grouping column.
        side_col: Name of the side column.

    Returns:
        Tuple of (filtered DataFrame, list of feature column names).
    """
    schema = load_feature_schema(schema_path)

    # Forbidden columns = unavailable + aux_targets
    forbidden = set(schema["inference_unavailable"]) | set(schema["auxiliary_targets"])
    # Never remove the target itself (we need it for training)
    forbidden.discard(target_col)
    # Never remove grouping/side columns (needed for splitting)
    forbidden.discard(group_col)
    forbidden.discard(side_col)

    # Identify feature columns (all columns except group, side, target, forbidden)
    all_cols = set(df.columns)
    metadata_cols = {group_col, side_col, target_col}
    feature_cols = sorted(all_cols - forbidden - metadata_cols)

    # Verify no leakage
    leaked = sorted(forbidden & set(feature_cols))
    if leaked:
        raise ValueError(f"Feature leakage detected: {leaked}")

    # Select columns for output
    keep_cols = [group_col, side_col, target_col] + feature_cols
    existing_cols = [c for c in keep_cols if c in df.columns]
    result = df.select(existing_cols)

    actual_feature_cols = [c for c in feature_cols if c in df.columns]

    return result, actual_feature_cols


def validate_feature_matrix(
    df: pl.DataFrame,
    feature_cols: list[str],
    target_col: str = "kl_grade",
    group_col: str = "patient_id",
) -> list[str]:
    """Validate feature matrix integrity.

    Returns:
        List of warnings (empty = all good).
    """
    warnings: list[str] = []

    # Check no NaN in target
    null_count = df[target_col].null_count()
    if null_count > 0:
        warnings.append(f"Target column has {null_count} null values")

    # Check feature missingness
    for col in feature_cols:
        if col not in df.columns:
            warnings.append(f"Expected feature '{col}' not found in DataFrame")
            continue
        null_pct = df[col].null_count() / len(df) * 100
        if null_pct > 50:
            warnings.append(f"Feature '{col}' has {null_pct:.1f}% missing values")

    # Check minimum sample count per KL grade
    for grade in range(5):
        count = len(df.filter(pl.col(target_col) == grade))
        if count < 10:
            warnings.append(
                f"KL grade {grade} has only {count} samples (minimum: 10)"
            )

    return warnings
