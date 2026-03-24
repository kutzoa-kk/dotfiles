"""Tests for data validation module."""

import pytest

from src.schema.data_validation import validate_data


class TestValidateData:
    """Tests for data validation."""

    def test_passes_with_valid_data(
        self, sample_config, sample_data_files, feature_schema_path
    ):
        """Validation passes with correctly structured data."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )
        errors = validate_data(sample_config)
        assert len(errors) == 0

    def test_fails_on_missing_inbody(
        self, sample_config, feature_schema_path
    ):
        """Validation fails when InBody file is missing."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = "/nonexistent/inbody.csv"
        sample_config.data.gait_features_path = "/nonexistent/gait.parquet"

        with pytest.raises(ValueError, match="Data validation failed"):
            validate_data(sample_config)

    def test_fails_on_missing_schema(self, sample_config):
        """Validation returns errors when schema file is missing."""
        sample_config.data.schema_path = "/nonexistent/schema.yaml"
        errors = validate_data(sample_config)
        assert len(errors) > 0
