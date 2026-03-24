"""Gait cycle feature aggregator.

Aggregates gait-cycle-level measurements to session level using
configurable statistics (mean, std, median, IQR, etc.).

Designed for 100 Hz knee joint angle time-series data.
Zero values represent non-contact / valid zero readings.
"""

import polars as pl


def aggregate_gait_cycles(
    cycle_df: pl.DataFrame,
    group_cols: list[str],
    feature_cols: list[str],
    stats: list[str] | None = None,
) -> pl.DataFrame:
    """Aggregate gait-cycle-level features to session level.

    Args:
        cycle_df: DataFrame with one row per gait cycle.
        group_cols: Columns that define a single session
                    (e.g., ["patient_id", "side", "visit_date"]).
        feature_cols: Columns to aggregate.
        stats: Statistics to compute. Defaults to ["mean", "std"].

    Returns:
        DataFrame with one row per session, columns named
        "{feature}_{stat}" (e.g., "knee_flexion_mean", "knee_flexion_std").
    """
    if stats is None:
        stats = ["mean", "std"]

    agg_exprs = []
    for stat_name in stats:
        for col in feature_cols:
            expr = _get_agg_expr(col, stat_name)
            agg_exprs.append(expr.alias(f"{col}_{stat_name}"))

    return cycle_df.group_by(group_cols).agg(agg_exprs)


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
        case "range":
            return pl.col(col).max() - pl.col(col).min()
        case "iqr":
            return pl.col(col).quantile(0.75) - pl.col(col).quantile(0.25)
        case _:
            raise ValueError(f"Unknown statistic: {stat}")
