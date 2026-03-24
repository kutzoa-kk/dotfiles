"""Tests for leakage detection module."""

import pytest

from src.schema.leakage_check import check_feature_leakage, check_target_not_in_features


class TestCheckFeatureLeakage:
    """Tests for feature leakage detection."""

    def test_passes_with_clean_features(
        self, sample_config, feature_schema_path
    ):
        """No error when features are clean."""
        sample_config.data.schema_path = str(feature_schema_path)
        clean_features = ["gender", "walk_feature_000", "step_feature_000"]
        # Should not raise
        check_feature_leakage(sample_config, feature_columns=clean_features)

    def test_detects_leaked_feature(
        self, sample_config, feature_schema_path
    ):
        """Raises ValueError when unavailable feature is detected."""
        sample_config.data.schema_path = str(feature_schema_path)
        leaked_features = ["gender", "smi", "walk_feature_000"]
        with pytest.raises(ValueError, match="LEAKAGE DETECTED"):
            check_feature_leakage(
                sample_config, feature_columns=leaked_features
            )

    def test_detects_username_as_leak(
        self, sample_config, feature_schema_path
    ):
        """Username (subject ID) is detected as leaked feature."""
        sample_config.data.schema_path = str(feature_schema_path)
        leaked_features = ["gender", "username"]
        with pytest.raises(ValueError, match="LEAKAGE DETECTED"):
            check_feature_leakage(
                sample_config, feature_columns=leaked_features
            )

    def test_schema_not_found_raises(self, sample_config):
        """Raises FileNotFoundError when schema file is missing."""
        sample_config.data.schema_path = "/nonexistent/path.yaml"
        with pytest.raises(FileNotFoundError):
            check_feature_leakage(
                sample_config, feature_columns=["gender"]
            )


class TestCheckTargetNotInFeatures:
    """Tests for target-in-features detection."""

    def test_passes_when_target_absent(self):
        """No error when target is not in features."""
        check_target_not_in_features(
            "sarcopenia_risk_score", ["gender", "walk_feature_000"]
        )

    def test_raises_when_target_present(self):
        """Raises ValueError when target is found in features."""
        with pytest.raises(ValueError, match="LEAKAGE DETECTED"):
            check_target_not_in_features(
                "sarcopenia_risk_score",
                ["gender", "sarcopenia_risk_score"],
            )
