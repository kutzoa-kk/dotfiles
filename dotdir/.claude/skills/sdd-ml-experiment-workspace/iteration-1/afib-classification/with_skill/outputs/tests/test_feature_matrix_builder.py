"""Tests for feature matrix builder."""

import numpy as np
import polars as pl
import pytest

from src.features.feature_matrix_builder import build_feature_matrix


class TestBuildFeatureMatrix:
    """Tests for the build_feature_matrix function."""

    def test_returns_three_components(self, sample_config):
        """Feature matrix builder returns (X, y, groups)."""
        x, y, groups = build_feature_matrix(sample_config)
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert isinstance(groups, np.ndarray)

    def test_excludes_unavailable_features(self, sample_config):
        """No inference_unavailable features appear in the matrix."""
        x, _, _ = build_feature_matrix(sample_config)
        # X should have 24 features (all inference_available ones)
        # It should NOT have record_id, af_label, diagnosis_date, cardiologist_notes
        assert x.shape[1] == 24

    def test_preserves_row_count(self, sample_config):
        """Feature count matches target and groups length."""
        x, y, groups = build_feature_matrix(sample_config)
        assert x.shape[0] == len(y)
        assert x.shape[0] == len(groups)

    def test_target_is_binary(self, sample_config):
        """Target values are binary (0 or 1)."""
        _, y, _ = build_feature_matrix(sample_config)
        unique_values = set(np.unique(y))
        assert unique_values.issubset({0, 1})

    def test_features_are_numeric(self, sample_config):
        """All feature values are numeric."""
        x, _, _ = build_feature_matrix(sample_config)
        assert x.dtype in (np.float64, np.float32, np.int64, np.int32)
