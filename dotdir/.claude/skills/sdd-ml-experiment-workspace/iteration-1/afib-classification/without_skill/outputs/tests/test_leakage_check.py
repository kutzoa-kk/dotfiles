"""Tests for leakage check module."""

from pathlib import Path

import pytest

from src.schema.leakage_check import (
    CheckResult,
    check_feature_leakage,
    check_split_subject_overlap,
)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "src" / "schema" / "feature_availability.yaml"


class TestCheckFeatureLeakage:
    def test_no_leakage_with_clean_features(self) -> None:
        clean_features = [
            "rr_mean", "rr_std", "rr_rmssd", "p_wave_amplitude",
            "qrs_duration", "hrv_sdnn", "heart_rate_mean",
        ]
        result = check_feature_leakage(SCHEMA_PATH, clean_features)
        assert result.passed is True

    def test_leakage_detected_with_record_id(self) -> None:
        leaked_features = ["rr_mean", "rr_std", "record_id"]
        result = check_feature_leakage(SCHEMA_PATH, leaked_features)
        assert result.passed is False
        assert "record_id" in result.message

    def test_leakage_detected_with_target(self) -> None:
        leaked_features = ["rr_mean", "af_label"]
        result = check_feature_leakage(SCHEMA_PATH, leaked_features)
        assert result.passed is False
        assert "af_label" in result.message

    def test_leakage_detected_with_diagnosis_date(self) -> None:
        leaked_features = ["rr_mean", "diagnosis_date"]
        result = check_feature_leakage(SCHEMA_PATH, leaked_features)
        assert result.passed is False

    def test_leakage_detected_with_notes(self) -> None:
        leaked_features = ["rr_mean", "cardiologist_notes"]
        result = check_feature_leakage(SCHEMA_PATH, leaked_features)
        assert result.passed is False

    def test_empty_features_passes(self) -> None:
        result = check_feature_leakage(SCHEMA_PATH, [])
        assert result.passed is True


class TestCheckSplitSubjectOverlap:
    def test_no_overlap(self) -> None:
        split_index = {"r1": 0, "r2": 1, "r3": 2}
        result = check_split_subject_overlap(split_index, "record_id")
        assert result.passed is True

    def test_check_result_str(self) -> None:
        cr = CheckResult("Test Check", True, "All good")
        assert "[PASS]" in str(cr)

        cr_fail = CheckResult("Test Check", False, "Something wrong")
        assert "[FAIL]" in str(cr_fail)
