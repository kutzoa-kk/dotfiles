"""Tests for gait cycle aggregator."""

import polars as pl
import pytest

from src.features.gait_cycle_aggregator import aggregate_gait_cycles


class TestAggregateGaitCycles:
    """Tests for gait cycle aggregation."""

    def test_aggregates_to_session_level(self):
        """Reduces multiple gait cycles to one row per session."""
        cycle_df = pl.DataFrame({
            "patient_id": ["P001"] * 5 + ["P002"] * 5,
            "side": ["L"] * 5 + ["R"] * 5,
            "knee_flexion": [10.0, 12.0, 11.0, 13.0, 9.0,
                             20.0, 22.0, 21.0, 23.0, 19.0],
        })

        result = aggregate_gait_cycles(
            cycle_df,
            group_cols=["patient_id", "side"],
            feature_cols=["knee_flexion"],
            stats=["mean", "std"],
        )

        assert len(result) == 2
        assert "knee_flexion_mean" in result.columns
        assert "knee_flexion_std" in result.columns

    def test_default_stats(self):
        """Uses mean and std by default."""
        cycle_df = pl.DataFrame({
            "patient_id": ["P001"] * 3,
            "value": [1.0, 2.0, 3.0],
        })

        result = aggregate_gait_cycles(
            cycle_df,
            group_cols=["patient_id"],
            feature_cols=["value"],
        )

        assert "value_mean" in result.columns
        assert "value_std" in result.columns

    def test_multiple_stats(self):
        """Computes multiple statistics per feature."""
        cycle_df = pl.DataFrame({
            "patient_id": ["P001"] * 5,
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        result = aggregate_gait_cycles(
            cycle_df,
            group_cols=["patient_id"],
            feature_cols=["value"],
            stats=["mean", "std", "median", "min", "max"],
        )

        assert "value_mean" in result.columns
        assert "value_median" in result.columns
        assert "value_min" in result.columns
        assert "value_max" in result.columns

    def test_raises_on_unknown_stat(self):
        """Raises ValueError for unknown statistic."""
        cycle_df = pl.DataFrame({
            "patient_id": ["P001"] * 3,
            "value": [1.0, 2.0, 3.0],
        })

        with pytest.raises(ValueError, match="Unknown statistic"):
            aggregate_gait_cycles(
                cycle_df,
                group_cols=["patient_id"],
                feature_cols=["value"],
                stats=["unknown_stat"],
            )
