"""Tests for leakage and split integrity checker."""

from pathlib import Path

import pandas as pd
import pytest

from src.schema.leakage_check import (
    CheckResult,
    check_feature_leakage,
    check_side_colocation,
    check_split_subject_overlap,
    check_temporal_holdout_integrity,
)


@pytest.fixture
def schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "src" / "schema" / "feature_availability.yaml"


@pytest.fixture
def clean_feature_columns() -> list[str]:
    """Feature columns with NO leakage."""
    return ["age", "sex", "knee_flex_max", "knee_rom", "cadence", "gait_speed"]


@pytest.fixture
def leaked_feature_columns() -> list[str]:
    """Feature columns WITH leakage (includes kl_grade)."""
    return ["age", "sex", "knee_flex_max", "kl_grade", "patient_id"]


class TestFeatureLeakage:
    def test_no_leakage_detected(
        self, schema_path: Path, clean_feature_columns: list[str]
    ) -> None:
        result = check_feature_leakage(schema_path, clean_feature_columns)
        assert result.passed is True

    def test_leakage_detected(
        self, schema_path: Path, leaked_feature_columns: list[str]
    ) -> None:
        result = check_feature_leakage(schema_path, leaked_feature_columns)
        assert result.passed is False

    def test_returns_check_result(
        self, schema_path: Path, clean_feature_columns: list[str]
    ) -> None:
        result = check_feature_leakage(schema_path, clean_feature_columns)
        assert isinstance(result, CheckResult)


class TestSplitSubjectOverlap:
    def test_no_overlap(self) -> None:
        split_index = {"P001": 0, "P002": 1, "P003": 2}
        df = pd.DataFrame({"patient_id": ["P001", "P002", "P003"]})
        result = check_split_subject_overlap(split_index, df, "patient_id")
        assert result.passed is True

    def test_returns_check_result(self) -> None:
        split_index = {"P001": 0}
        df = pd.DataFrame({"patient_id": ["P001"]})
        result = check_split_subject_overlap(split_index, df, "patient_id")
        assert isinstance(result, CheckResult)


class TestSideColocation:
    def test_sides_colocated(self) -> None:
        """L/R sides for same patient should be in same split."""
        df = pd.DataFrame({
            "patient_id": ["P001", "P001", "P002", "P002"],
            "side": ["L", "R", "L", "R"],
        })
        split_index = {"P001": 0, "P002": 1}
        result = check_side_colocation(df, split_index, "patient_id")
        assert result.passed is True

    def test_missing_patient_detected(self) -> None:
        df = pd.DataFrame({
            "patient_id": ["P001", "P001", "P003"],
            "side": ["L", "R", "L"],
        })
        split_index = {"P001": 0}  # P003 missing
        result = check_side_colocation(df, split_index, "patient_id")
        assert result.passed is False


class TestTemporalHoldoutIntegrity:
    def test_clean_temporal_split(self) -> None:
        df = pd.DataFrame({
            "patient_id": ["P001", "P002", "P003"],
            "visit_date": ["2023-01-15", "2023-06-20", "2024-03-10"],
        })
        result = check_temporal_holdout_integrity(df, "patient_id")
        assert result.passed is True

    def test_temporal_leak_detected(self) -> None:
        """Patient appears in both train and test periods."""
        df = pd.DataFrame({
            "patient_id": ["P001", "P001"],
            "visit_date": ["2023-01-15", "2024-06-20"],
        })
        result = check_temporal_holdout_integrity(df, "patient_id")
        assert result.passed is False
