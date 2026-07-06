"""Tests for data validation."""

import numpy as np
import polars as pl
import pytest

from src.schema.data_validation import validate_data, ValidationResult


class TestValidateData:
    """Tests for data validation function."""

    def test_valid_data_passes(self, sample_ecg_data):
        """Valid data passes validation."""
        result = validate_data(sample_ecg_data)
        assert isinstance(result, ValidationResult)
        assert result.is_valid

    def test_missing_required_column_fails(self):
        """Missing required columns cause validation failure."""
        df = pl.DataFrame({"some_column": [1, 2, 3]})
        result = validate_data(df)
        assert not result.is_valid
        assert any("record_id" in e for e in result.errors)

    def test_non_binary_label_fails(self):
        """Non-binary af_label causes validation failure."""
        df = pl.DataFrame({
            "record_id": ["r1", "r2", "r3"],
            "af_label": [0, 1, 2],  # 2 is invalid
        })
        result = validate_data(df)
        assert not result.is_valid

    def test_duplicate_records_warned(self):
        """Duplicate record_ids produce warnings."""
        np.random.seed(42)
        df = pl.DataFrame({
            "record_id": ["r1", "r1", "r2"],
            "af_label": [0, 1, 0],
        })
        result = validate_data(df)
        assert any("Duplicate" in w for w in result.warnings)


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_is_frozen(self):
        """ValidationResult is immutable."""
        result = ValidationResult(is_valid=True, errors=(), warnings=())
        with pytest.raises(AttributeError):
            result.is_valid = False
