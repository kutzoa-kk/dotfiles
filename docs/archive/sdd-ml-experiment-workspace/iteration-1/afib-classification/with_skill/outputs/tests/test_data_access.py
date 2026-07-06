"""Tests for data access layer."""

import polars as pl
import pytest

from src.data_access import load_data, load_raw


class TestLoadData:
    """Tests for the load_data function."""

    def test_returns_dataframe(self, sample_config):
        """load_data returns a Polars DataFrame."""
        df = load_data(sample_config)
        assert isinstance(df, pl.DataFrame)

    def test_contains_required_columns(self, sample_config):
        """Loaded data contains record_id and af_label."""
        df = load_data(sample_config)
        assert "record_id" in df.columns
        assert "af_label" in df.columns

    def test_non_empty_result(self, sample_config):
        """Loaded data has rows."""
        df = load_data(sample_config)
        assert len(df) > 0

    def test_raises_on_missing_file(self, sample_config):
        """Raises FileNotFoundError for non-existent file."""
        from omegaconf import OmegaConf

        bad_cfg = OmegaConf.merge(
            sample_config,
            {"data": {"ecg_features_path": "/nonexistent/path.parquet"}},
        )
        with pytest.raises(FileNotFoundError):
            load_data(bad_cfg)


class TestLoadRaw:
    """Tests for the load_raw function."""

    def test_loads_parquet(self, sample_config):
        """Can load a parquet file."""
        df = load_raw(sample_config.data.ecg_features_path)
        assert isinstance(df, pl.DataFrame)

    def test_loads_csv(self, sample_config):
        """Can load a CSV file."""
        df = load_raw(sample_config.data.clinical_labels_path)
        assert isinstance(df, pl.DataFrame)

    def test_raises_on_unsupported_format(self, tmp_path):
        """Raises ValueError for unsupported file formats."""
        bad_file = tmp_path / "data.xlsx"
        bad_file.touch()
        with pytest.raises(ValueError, match="Unsupported format"):
            load_raw(str(bad_file))
