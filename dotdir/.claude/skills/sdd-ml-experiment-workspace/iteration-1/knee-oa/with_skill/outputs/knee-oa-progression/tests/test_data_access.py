"""Tests for data access layer."""

import polars as pl
import pytest

from src.data_access import load_raw, save_processed


class TestLoadRaw:
    """Tests for the load_raw function."""

    def test_raises_on_missing_file(self):
        """Raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_raw("nonexistent.csv", raw_dir="/tmp/nonexistent_dir")

    def test_raises_on_unsupported_format(self, tmp_output_dir):
        """Raises ValueError for unsupported file format."""
        bad_file = tmp_output_dir / "data.xlsx"
        bad_file.write_text("")
        with pytest.raises(ValueError, match="Unsupported format"):
            load_raw("data.xlsx", raw_dir=str(tmp_output_dir))

    def test_loads_csv(self, tmp_output_dir):
        """Successfully loads a CSV file."""
        csv_path = tmp_output_dir / "test.csv"
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.write_csv(csv_path)

        result = load_raw("test.csv", raw_dir=str(tmp_output_dir))
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2

    def test_loads_parquet(self, tmp_output_dir):
        """Successfully loads a Parquet file."""
        parquet_path = tmp_output_dir / "test.parquet"
        df = pl.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        df.write_parquet(parquet_path)

        result = load_raw("test.parquet", raw_dir=str(tmp_output_dir))
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2


class TestSaveProcessed:
    """Tests for the save_processed function."""

    def test_saves_parquet(self, tmp_output_dir):
        """Saves DataFrame as Parquet file."""
        df = pl.DataFrame({"a": [1, 2, 3]})
        path = save_processed(df, "test.parquet", processed_dir=str(tmp_output_dir))
        assert path.exists()
        loaded = pl.read_parquet(path)
        assert len(loaded) == 3

    def test_creates_directories(self, tmp_output_dir):
        """Creates parent directories if they don't exist."""
        df = pl.DataFrame({"a": [1]})
        path = save_processed(
            df, "subdir/test.parquet", processed_dir=str(tmp_output_dir)
        )
        assert path.exists()
