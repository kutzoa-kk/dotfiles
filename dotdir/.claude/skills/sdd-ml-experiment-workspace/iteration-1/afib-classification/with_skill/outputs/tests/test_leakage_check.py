"""Tests for leakage check."""

import pytest

from src.schema.leakage_check import check_feature_leakage, validate_feature_set


class TestCheckFeatureLeakage:
    """Tests for feature leakage detection."""

    def test_no_leakage_returns_empty(self, feature_schema_path):
        """Clean feature set returns empty leakage list."""
        features = ["rr_mean", "rr_std", "heart_rate_mean"]
        leaked = check_feature_leakage(features, feature_schema_path)
        assert leaked == []

    def test_detects_leakage(self, feature_schema_path):
        """Leaked features are detected."""
        features = ["rr_mean", "af_label", "record_id"]
        leaked = check_feature_leakage(features, feature_schema_path)
        assert "af_label" in leaked
        assert "record_id" in leaked

    def test_raises_on_missing_schema(self):
        """Raises FileNotFoundError for missing schema."""
        with pytest.raises(FileNotFoundError):
            check_feature_leakage(["rr_mean"], "/nonexistent/schema.yaml")


class TestValidateFeatureSet:
    """Tests for feature set validation."""

    def test_categorizes_features(self, feature_schema_path):
        """Features are correctly categorized."""
        features = ["rr_mean", "af_label", "unknown_feature"]
        result = validate_feature_set(features, feature_schema_path)

        assert "rr_mean" in result["available"]
        assert "af_label" in result["unavailable"]
        assert "unknown_feature" in result["unknown"]
