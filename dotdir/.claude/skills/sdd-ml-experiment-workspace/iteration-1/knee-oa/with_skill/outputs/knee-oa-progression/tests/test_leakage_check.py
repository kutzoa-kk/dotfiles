"""Tests for leakage check."""

import pytest

from src.schema.leakage_check import check_feature_leakage, validate_split_integrity


class TestCheckFeatureLeakage:
    """Tests for feature leakage detection."""

    def test_clean_features_pass(self, feature_schema_path):
        """Clean feature set passes leakage check."""
        clean_features = ["knee_flexion_mean", "knee_flexion_std", "age", "bmi"]
        is_clean, leaked = check_feature_leakage(clean_features, feature_schema_path)
        assert is_clean is True
        assert len(leaked) == 0

    def test_detects_target_leakage(self, feature_schema_path):
        """Detects when target variable is in feature set."""
        leaked_features = ["knee_flexion_mean", "kl_grade"]
        is_clean, leaked = check_feature_leakage(leaked_features, feature_schema_path)
        assert is_clean is False
        assert "kl_grade" in leaked

    def test_detects_id_leakage(self, feature_schema_path):
        """Detects when patient_id is in feature set."""
        leaked_features = ["knee_flexion_mean", "patient_id"]
        is_clean, leaked = check_feature_leakage(leaked_features, feature_schema_path)
        assert is_clean is False
        assert "patient_id" in leaked

    def test_detects_multiple_leaks(self, feature_schema_path):
        """Detects multiple leaked columns."""
        leaked_features = ["patient_id", "kl_grade", "visit_date", "age"]
        is_clean, leaked = check_feature_leakage(leaked_features, feature_schema_path)
        assert is_clean is False
        assert len(leaked) == 3  # patient_id, kl_grade, visit_date


class TestValidateSplitIntegrity:
    """Tests for split integrity validation."""

    def test_clean_split_passes(self):
        """Non-overlapping splits pass validation."""
        train_groups = {"P001", "P002", "P003"}
        val_groups = {"P004", "P005"}
        is_clean, overlap = validate_split_integrity(train_groups, val_groups)
        assert is_clean is True
        assert len(overlap) == 0

    def test_detects_overlap(self):
        """Detects overlapping groups between train and val."""
        train_groups = {"P001", "P002", "P003"}
        val_groups = {"P003", "P004"}
        is_clean, overlap = validate_split_integrity(train_groups, val_groups)
        assert is_clean is False
        assert "P003" in overlap
