# Feature Engineering Templates (src/features/)

## Feature Matrix Builder

The central module that combines all data sources into a training-ready matrix.

```python
"""Feature matrix builder.

Combines raw data sources into a single feature matrix suitable for model training.
Only includes features marked as inference_available in feature_availability.yaml.
"""

import logging
from pathlib import Path

import polars as pl
import yaml
from omegaconf import DictConfig

from src.data_access import load_data

logger = logging.getLogger(__name__)


def load_feature_schema(schema_path: str | Path) -> dict:
    """Load feature availability schema."""
    with open(schema_path) as f:
        return yaml.safe_load(f)


def build_feature_matrix(
    cfg: DictConfig,
) -> tuple[pl.DataFrame, pl.Series, pl.Series]:
    """Build feature matrix from raw data.

    Returns:
        Tuple of (features_df, target_series, group_series)
        - features_df: Only inference_available columns
        - target_series: The prediction target
        - group_series: Subject IDs for GroupKFold splitting
    """
    # 1. Load raw data
    df = load_data(cfg)
    logger.info(f"Loaded {len(df)} rows")

    # 2. Load feature schema
    schema = load_feature_schema(cfg.data.schema_path)
    available = set(schema["features"]["inference_available"])
    unavailable = set(schema["features"]["inference_unavailable"])

    # 3. Validate no leakage
    actual_cols = set(df.columns)
    feature_cols = sorted(actual_cols & available)
    leaked = actual_cols & unavailable
    if leaked:
        raise ValueError(
            f"Feature matrix contains inference_unavailable columns: {leaked}"
        )

    logger.info(f"Using {len(feature_cols)} inference_available features")

    # 4. Extract components
    features = df.select(feature_cols)
    target = df.get_column("{{target_column}}")
    groups = df.get_column("{{subject_id_field}}")

    return features, target, groups
```

## Step Aggregator (for time-series / multi-observation data)

When data has multiple observations per walk/session/trial that need aggregation.

```python
"""Step-level feature aggregator.

Aggregates step-level measurements to walk/session level using
configurable statistics (mean, std, median, IQR, etc.).
"""

import polars as pl


AGGREGATION_STATS = {
    "mean": pl.col("*").mean(),
    "std": pl.col("*").std(),
    "median": pl.col("*").median(),
    "q25": pl.col("*").quantile(0.25),
    "q75": pl.col("*").quantile(0.75),
    "min": pl.col("*").min(),
    "max": pl.col("*").max(),
}


def aggregate_steps(
    step_df: pl.DataFrame,
    group_cols: list[str],
    feature_cols: list[str],
    stats: list[str] | None = None,
) -> pl.DataFrame:
    """Aggregate step-level features to walk/session level.

    Args:
        step_df: DataFrame with one row per step.
        group_cols: Columns that define a single walk/session
                    (e.g., ["username", "test_date_time"]).
        feature_cols: Columns to aggregate.
        stats: Statistics to compute. Defaults to ["mean", "std"].

    Returns:
        DataFrame with one row per walk/session, columns named
        "{feature}_{stat}" (e.g., "cop_x_mean", "cop_x_std").
    """
    if stats is None:
        stats = ["mean", "std"]

    agg_exprs = []
    for stat_name in stats:
        for col in feature_cols:
            expr = _get_agg_expr(col, stat_name)
            agg_exprs.append(expr.alias(f"{col}_{stat_name}"))

    return step_df.group_by(group_cols).agg(agg_exprs)


def _get_agg_expr(col: str, stat: str) -> pl.Expr:
    """Get Polars aggregation expression for a column and statistic."""
    match stat:
        case "mean":
            return pl.col(col).mean()
        case "std":
            return pl.col(col).std()
        case "median":
            return pl.col(col).median()
        case "q25":
            return pl.col(col).quantile(0.25)
        case "q75":
            return pl.col(col).quantile(0.75)
        case "min":
            return pl.col(col).min()
        case "max":
            return pl.col(col).max()
        case _:
            raise ValueError(f"Unknown statistic: {stat}")
```

## data_access.py (Polars version)

```python
"""Centralized data access layer (Polars).

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.
"""

from pathlib import Path

import polars as pl
from omegaconf import DictConfig


def load_data(cfg: DictConfig) -> pl.DataFrame:
    """Load and join all data sources defined in config.

    Args:
        cfg: Hydra config with data.raw_dir, data source paths, and join keys.

    Returns:
        Joined DataFrame with all data sources.
    """
    # {{Implementation depends on interview answers}}
    # Example:
    # labels = pl.read_csv(Path(cfg.data.label_path))
    # features = pl.read_parquet(Path(cfg.data.feature_path))
    # return labels.join(features, on=cfg.data.join_keys, how="inner")
    raise NotImplementedError("Implement data loading based on your data sources")


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
```

## split_generator.py

```python
"""Split generator with integrity validation.

Creates CV and holdout splits respecting subject grouping.
"""

import json
from pathlib import Path

import numpy as np
from omegaconf import DictConfig
from sklearn.model_selection import GroupKFold


def generate_splits(
    cfg: DictConfig, groups: np.ndarray
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate CV splits respecting group constraints.

    Args:
        cfg: Config with split.method, split.n_splits, split.group_key.
        groups: Array of group labels (subject IDs).

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
```
