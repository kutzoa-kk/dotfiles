"""Tests for feature matrix builder."""

import polars as pl
import pytest

from src.features.feature_matrix_builder import (
    build_feature_matrix,
    load_feature_schema,
)


class TestLoadFeatureSchema:
    """Tests for feature schema loading."""

    def test_loads_yaml(self, feature_schema_path):
        """Successfully loads feature availability YAML."""
        schema = load_feature_schema(feature_schema_path)
        assert "features" in schema
        assert "inference_available" in schema["features"]
        assert "inference_unavailable" in schema["features"]

    def test_contains_expected_features(self, feature_schema_path):
        """Schema contains expected feature groups."""
        schema = load_feature_schema(feature_schema_path)
        available = schema["features"]["inference_available"]
        assert "knee_flexion_mean" in available
        assert "age" in available
        assert "gait_speed_mean" in available

    def test_unavailable_includes_target(self, feature_schema_path):
        """KL grade is marked as inference_unavailable."""
        schema = load_feature_schema(feature_schema_path)
        unavailable = schema["features"]["inference_unavailable"]
        assert "kl_grade" in unavailable
        assert "patient_id" in unavailable


class TestBuildFeatureMatrix:
    """Tests for the build_feature_matrix function.

    NOTE: These tests require data loading to be implemented.
    They are written to guide implementation (TDD RED phase).
    """

    def test_returns_three_components(self, sample_config):
        """Feature matrix builder returns (features, target, groups)."""
        # This test will fail until data loading is implemented
        # with real data or mocked data_access.load_data
        with pytest.raises((NotImplementedError, FileNotFoundError)):
            features, target, groups = build_feature_matrix(sample_config)

    def test_excludes_unavailable_features(self, sample_config):
        """No inference_unavailable features appear in the matrix."""
        # When implemented, verify:
        # features, _, _ = build_feature_matrix(sample_config)
        # assert "patient_id" not in features.columns
        # assert "kl_grade" not in features.columns
        # assert "visit_date" not in features.columns
        pass

    def test_preserves_row_count(self, sample_config):
        """Feature, target, and groups lengths match."""
        # When implemented, verify:
        # features, target, groups = build_feature_matrix(sample_config)
        # assert len(features) == len(target)
        # assert len(features) == len(groups)
        pass
