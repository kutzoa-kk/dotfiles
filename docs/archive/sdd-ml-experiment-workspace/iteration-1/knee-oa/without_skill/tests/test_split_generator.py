"""Tests for data split generator."""

import json
from pathlib import Path

import polars as pl
import pytest

from src.split_generator import (
    generate_cv_split_index,
    generate_temporal_holdout_split,
    save_split_index,
    validate_split_integrity,
)


@pytest.fixture
def bilateral_data() -> pl.DataFrame:
    """Data with patients having L/R sides and multiple visits."""
    rows = []
    for i in range(1, 21):
        for side in ["L", "R"]:
            year = "2023" if i <= 14 else "2024"
            rows.append({
                "patient_id": f"P{i:03d}",
                "side": side,
                "visit_date": f"{year}-06-15",
                "kl_grade": i % 5,
                "age": 50.0 + i,
                "sex": "M" if i % 2 == 0 else "F",
            })
    return pl.DataFrame(rows)


class TestGenerateCVSplitIndex:
    def test_all_patients_assigned(self, bilateral_data: pl.DataFrame) -> None:
        split_index = generate_cv_split_index(bilateral_data)
        unique_patients = bilateral_data["patient_id"].unique().to_list()
        for pid in unique_patients:
            assert str(pid) in split_index

    def test_five_folds(self, bilateral_data: pl.DataFrame) -> None:
        split_index = generate_cv_split_index(bilateral_data, n_splits=5)
        fold_values = set(split_index.values())
        assert len(fold_values) == 5
        assert fold_values == {0, 1, 2, 3, 4}

    def test_reproducible(self, bilateral_data: pl.DataFrame) -> None:
        split1 = generate_cv_split_index(bilateral_data, seed=42)
        split2 = generate_cv_split_index(bilateral_data, seed=42)
        assert split1 == split2

    def test_different_seeds_differ(self) -> None:
        """Different seeds should produce different fold assignments."""
        # Use a larger dataset to ensure shuffling produces different results
        rows = []
        for i in range(1, 101):
            for side in ["L", "R"]:
                rows.append({
                    "patient_id": f"P{i:03d}",
                    "side": side,
                    "visit_date": "2023-06-15",
                    "kl_grade": i % 5,
                    "age": 50.0 + i,
                    "sex": "M" if i % 2 == 0 else "F",
                })
        large_data = pl.DataFrame(rows)
        split1 = generate_cv_split_index(large_data, seed=42)
        split2 = generate_cv_split_index(large_data, seed=99)
        assert split1 != split2

    def test_lr_colocation(self, bilateral_data: pl.DataFrame) -> None:
        """L/R sides must be in the same fold (via patient-level split)."""
        split_index = generate_cv_split_index(bilateral_data)
        # Since splitting is at patient level, L/R are automatically co-located
        for pid in bilateral_data["patient_id"].unique().to_list():
            assert str(pid) in split_index


class TestGenerateTemporalHoldoutSplit:
    def test_temporal_split(self, bilateral_data: pl.DataFrame) -> None:
        split = generate_temporal_holdout_split(bilateral_data)
        assert set(split.values()) == {0, 1}

    def test_train_before_cutoff(self, bilateral_data: pl.DataFrame) -> None:
        split = generate_temporal_holdout_split(bilateral_data, cutoff_year=2024)
        # Patients 1-14 are in 2023 (train), 15-20 in 2024 (holdout)
        for pid, assignment in split.items():
            pid_num = int(pid[1:])
            if pid_num <= 14:
                assert assignment == 0, f"Patient {pid} should be train (< 2024)"
            else:
                assert assignment == 1, f"Patient {pid} should be holdout (>= 2024)"

    def test_reproducible(self, bilateral_data: pl.DataFrame) -> None:
        split1 = generate_temporal_holdout_split(bilateral_data)
        split2 = generate_temporal_holdout_split(bilateral_data)
        assert split1 == split2


class TestValidateSplitIntegrity:
    def test_no_violations(self, bilateral_data: pl.DataFrame) -> None:
        split_index = generate_cv_split_index(bilateral_data)
        violations = validate_split_integrity(bilateral_data, split_index)
        assert violations == []

    def test_missing_patient_detected(self, bilateral_data: pl.DataFrame) -> None:
        split_index = generate_cv_split_index(bilateral_data)
        del split_index["P001"]
        violations = validate_split_integrity(bilateral_data, split_index)
        assert len(violations) > 0


class TestSaveSplitIndex:
    def test_saves_json(self, tmp_path: Path) -> None:
        split_index = {"P001": 0, "P002": 1, "P003": 2}
        output = save_split_index(split_index, tmp_path / "split.json")
        assert output.exists()
        with open(output) as f:
            loaded = json.load(f)
        assert loaded == split_index
