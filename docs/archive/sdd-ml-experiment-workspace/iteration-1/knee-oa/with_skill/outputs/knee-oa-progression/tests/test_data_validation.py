"""Tests for data validation."""

import numpy as np
import polars as pl
import pytest

from src.schema.data_validation import validate_clinical_metadata, validate_feature_matrix


class TestValidateClinicalMetadata:
    """Tests for clinical metadata validation."""

    def test_valid_data_passes(self):
        """Valid clinical metadata passes all checks."""
        df = pl.DataFrame({
            "patient_id": ["P001", "P002"],
            "side": ["L", "R"],
            "kl_grade": [1, 3],
            "age": [55, 67],
            "sex": ["M", "F"],
            "visit_date": ["2023-01-01", "2023-06-01"],
        })
        result = validate_clinical_metadata(df)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_columns_fails(self):
        """Missing required columns cause validation failure."""
        df = pl.DataFrame({
            "patient_id": ["P001"],
            "side": ["L"],
        })
        result = validate_clinical_metadata(df)
        assert result.is_valid is False
        assert any("Missing required columns" in e for e in result.errors)

    def test_invalid_kl_range_fails(self):
        """KL grade outside 0-4 causes validation failure."""
        df = pl.DataFrame({
            "patient_id": ["P001"],
            "side": ["L"],
            "kl_grade": [5],
            "age": [55],
            "sex": ["M"],
            "visit_date": ["2023-01-01"],
        })
        result = validate_clinical_metadata(df)
        assert result.is_valid is False

    def test_invalid_side_fails(self):
        """Invalid side values cause validation failure."""
        df = pl.DataFrame({
            "patient_id": ["P001"],
            "side": ["X"],
            "kl_grade": [2],
            "age": [55],
            "sex": ["M"],
            "visit_date": ["2023-01-01"],
        })
        result = validate_clinical_metadata(df)
        assert result.is_valid is False


class TestValidateFeatureMatrix:
    """Tests for feature matrix validation."""

    def test_valid_matrix_passes(self):
        """Valid feature matrix passes all checks."""
        features = pl.DataFrame({
            "f1": [1.0, 2.0, 3.0],
            "f2": [4.0, 5.0, 6.0],
        })
        target = pl.Series("kl_grade", [0, 2, 4])
        groups = pl.Series("patient_id", ["P001", "P002", "P003"])

        result = validate_feature_matrix(features, target, groups)
        assert result.is_valid is True

    def test_length_mismatch_fails(self):
        """Mismatched lengths cause validation failure."""
        features = pl.DataFrame({"f1": [1.0, 2.0]})
        target = pl.Series("kl_grade", [0, 2, 4])
        groups = pl.Series("patient_id", ["P001", "P002", "P003"])

        result = validate_feature_matrix(features, target, groups)
        assert result.is_valid is False

    def test_target_out_of_range_fails(self):
        """Target values outside 0-4 cause validation failure."""
        features = pl.DataFrame({"f1": [1.0, 2.0]})
        target = pl.Series("kl_grade", [0, 5])
        groups = pl.Series("patient_id", ["P001", "P002"])

        result = validate_feature_matrix(features, target, groups)
        assert result.is_valid is False
