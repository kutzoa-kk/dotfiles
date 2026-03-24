"""Tests for data split generator."""

import json
from pathlib import Path

import polars as pl
import pytest

from src.split_generator import (
    generate_holdout_split,
    generate_split_index,
    save_split_index,
    validate_split_integrity,
)


@pytest.fixture
def multi_record_data() -> pl.DataFrame:
    """Data with subjects having multiple ECG records."""
    return pl.DataFrame(
        {
            "record_id": [
                "r1", "r1", "r2", "r2", "r3", "r3",
                "r4", "r4", "r5", "r5", "r6", "r6",
                "r7", "r7", "r8", "r8", "r9", "r9", "r10", "r10",
            ],
            "af_label": [
                1, 1, 0, 0, 1, 1,
                0, 0, 1, 1, 0, 0,
                1, 1, 0, 0, 0, 0, 1, 1,
            ],
        }
    )


class TestGenerateSplitIndex:
    def test_all_subjects_assigned(self, multi_record_data: pl.DataFrame) -> None:
        split_index = generate_split_index(multi_record_data)
        unique_records = multi_record_data["record_id"].unique().to_list()
        for record_id in unique_records:
            assert str(record_id) in split_index

    def test_five_folds(self, multi_record_data: pl.DataFrame) -> None:
        split_index = generate_split_index(multi_record_data, n_splits=5)
        fold_values = set(split_index.values())
        assert len(fold_values) == 5
        assert fold_values == {0, 1, 2, 3, 4}

    def test_reproducible(self, multi_record_data: pl.DataFrame) -> None:
        split1 = generate_split_index(multi_record_data, seed=42)
        split2 = generate_split_index(multi_record_data, seed=42)
        assert split1 == split2

    def test_different_seeds_differ(self, multi_record_data: pl.DataFrame) -> None:
        split1 = generate_split_index(multi_record_data, seed=42)
        split2 = generate_split_index(multi_record_data, seed=99)
        assert split1 != split2


class TestValidateSplitIntegrity:
    def test_no_violations(self, multi_record_data: pl.DataFrame) -> None:
        split_index = generate_split_index(multi_record_data)
        violations = validate_split_integrity(multi_record_data, split_index)
        assert violations == []

    def test_missing_subject_detected(self, multi_record_data: pl.DataFrame) -> None:
        split_index = generate_split_index(multi_record_data)
        del split_index["r1"]
        violations = validate_split_integrity(multi_record_data, split_index)
        assert len(violations) > 0


@pytest.fixture
def holdout_data() -> pl.DataFrame:
    """20 subjects (10 AF, 10 non-AF) with 2 records each."""
    records = [f"r{i}" for i in range(1, 21)]
    af_labels = [1] * 10 + [0] * 10
    rows_record = []
    rows_af = []
    for r, af in zip(records, af_labels):
        rows_record.extend([r, r])
        rows_af.extend([af, af])
    return pl.DataFrame({"record_id": rows_record, "af_label": rows_af})


class TestGenerateHoldoutSplit:
    def test_holdout_two_groups(self, holdout_data: pl.DataFrame) -> None:
        split = generate_holdout_split(holdout_data)
        assert set(split.values()) == {0, 1}

    def test_holdout_approx_80_20(self, holdout_data: pl.DataFrame) -> None:
        split = generate_holdout_split(holdout_data, test_size=0.2)
        n_subjects = len(split)
        n_holdout = sum(1 for v in split.values() if v == 1)
        ratio = n_holdout / n_subjects
        assert 0.15 <= ratio <= 0.25, f"Holdout ratio {ratio:.2f} outside +/-5%"

    def test_holdout_af_stratified(self, holdout_data: pl.DataFrame) -> None:
        split = generate_holdout_split(holdout_data, test_size=0.2)
        # Build af map
        af_map: dict[str, int] = {}
        for row in holdout_data.iter_rows(named=True):
            af_map[row["record_id"]] = row["af_label"]
        # Check each set has both classes
        train_labels = {af_map[r] for r, v in split.items() if v == 0}
        holdout_labels = {af_map[r] for r, v in split.items() if v == 1}
        assert 0 in train_labels and 1 in train_labels
        assert 0 in holdout_labels and 1 in holdout_labels

    def test_holdout_reproducible(self, holdout_data: pl.DataFrame) -> None:
        split1 = generate_holdout_split(holdout_data, seed=123)
        split2 = generate_holdout_split(holdout_data, seed=123)
        assert split1 == split2


class TestSaveSplitIndex:
    def test_saves_json(self, tmp_path: Path) -> None:
        split_index = {"r1": 0, "r2": 1, "r3": 2}
        output = save_split_index(split_index, tmp_path / "split.json")
        assert output.exists()
        with open(output) as f:
            loaded = json.load(f)
        assert loaded == split_index
