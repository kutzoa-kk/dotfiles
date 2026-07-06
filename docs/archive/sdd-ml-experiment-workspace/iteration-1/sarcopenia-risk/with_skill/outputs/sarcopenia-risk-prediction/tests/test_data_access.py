"""Tests for data access module."""

import polars as pl
import pytest

from src.data_access import load_raw, load_raw_csv, load_raw_parquet, save_processed


class TestLoadRawCsv:
    """Tests for CSV loading."""

    def test_loads_csv_file(self, sample_data_files):
        """CSV file is loaded as Polars DataFrame."""
        df = load_raw_csv(str(sample_data_files["inbody_path"]))
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0

    def test_raises_on_missing_file(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_raw_csv("nonexistent/path.csv")


class TestLoadRawParquet:
    """Tests for Parquet loading."""

    def test_loads_parquet_file(self, sample_data_files):
        """Parquet file is loaded as Polars DataFrame."""
        df = load_raw_parquet(str(sample_data_files["gait_path"]))
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0

    def test_raises_on_missing_file(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_raw_parquet("nonexistent/path.parquet")


class TestLoadRaw:
    """Tests for generic raw file loader."""

    def test_loads_csv_by_extension(self, sample_data_files):
        """Automatically detects CSV format."""
        df = load_raw(
            "inbody.csv",
            raw_dir=str(sample_data_files["inbody_path"].parent),
        )
        assert isinstance(df, pl.DataFrame)

    def test_loads_parquet_by_extension(self, sample_data_files):
        """Automatically detects Parquet format."""
        df = load_raw(
            "gait_features.parquet",
            raw_dir=str(sample_data_files["gait_path"].parent),
        )
        assert isinstance(df, pl.DataFrame)

    def test_raises_on_unsupported_format(self, tmp_output_dir):
        """Raises ValueError for unsupported file formats."""
        bad_file = tmp_output_dir / "data.xlsx"
        bad_file.touch()
        with pytest.raises(ValueError, match="Unsupported format"):
            load_raw("data.xlsx", raw_dir=str(tmp_output_dir))


class TestSaveProcessed:
    """Tests for saving processed data."""

    def test_saves_parquet(self, tmp_output_dir):
        """Saves DataFrame as Parquet file."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        path = save_processed(
            df, "test.parquet", processed_dir=str(tmp_output_dir)
        )
        assert path.exists()

        loaded = pl.read_parquet(path)
        assert loaded.shape == df.shape
