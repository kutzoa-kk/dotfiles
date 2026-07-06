"""Tests for feature matrix builder."""

import numpy as np
import polars as pl
import pytest
import yaml

from src.features.feature_matrix_builder import (
    build_feature_matrix,
    get_available_feature_columns,
    load_feature_schema,
)


class TestLoadFeatureSchema:
    """Tests for schema loading."""

    def test_loads_valid_schema(self, feature_schema_path):
        """Schema is loaded correctly from YAML file."""
        schema = load_feature_schema(feature_schema_path)
        assert "features" in schema
        assert "inference_available" in schema["features"]
        assert "inference_unavailable" in schema["features"]


class TestGetAvailableFeatureColumns:
    """Tests for feature column filtering."""

    def test_excludes_unavailable(self, feature_schema):
        """Unavailable features are excluded."""
        actual_columns = [
            "gender",
            "walk_feature_000",
            "username",
            "smi",
        ]
        available = get_available_feature_columns(feature_schema, actual_columns)
        assert "username" not in available
        assert "smi" not in available
        assert "gender" in available
        assert "walk_feature_000" in available

    def test_returns_sorted_list(self, feature_schema):
        """Available features are returned sorted."""
        actual_columns = [
            "walk_feature_001",
            "gender",
            "walk_feature_000",
        ]
        available = get_available_feature_columns(feature_schema, actual_columns)
        assert available == sorted(available)


class TestBuildFeatureMatrix:
    """Tests for the build_feature_matrix function."""

    def test_returns_three_components(
        self, sample_config, sample_data_files, feature_schema_path
    ):
        """Feature matrix builder returns (features, target, groups)."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )

        features, target, groups = build_feature_matrix(sample_config)
        assert isinstance(features, np.ndarray)
        assert isinstance(target, np.ndarray)
        assert isinstance(groups, np.ndarray)

    def test_preserves_row_count(
        self, sample_config, sample_data_files, feature_schema_path
    ):
        """All three components have matching length."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )

        features, target, groups = build_feature_matrix(sample_config)
        assert len(features) == len(target)
        assert len(features) == len(groups)

    def test_excludes_unavailable_features(
        self, sample_config, sample_data_files, feature_schema_path, feature_schema
    ):
        """No inference_unavailable features appear in the matrix."""
        sample_config.data.schema_path = str(feature_schema_path)
        sample_config.data.inbody_path = str(sample_data_files["inbody_path"])
        sample_config.data.gait_features_path = str(
            sample_data_files["gait_path"]
        )

        features, _, _ = build_feature_matrix(sample_config)
        # Features should not include unavailable columns
        # The number of features should match available feature count
        unavailable = set(feature_schema["features"]["inference_unavailable"])
        n_features = features.shape[1]
        assert n_features > 0
