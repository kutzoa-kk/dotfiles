"""Tests for split generator."""

import numpy as np
import pytest

from src.split_generator import (
    generate_holdout_split,
    generate_splits,
    save_split_index,
)


class TestGenerateSplits:
    """Tests for CV split generation."""

    def test_correct_number_of_folds(self, sample_config):
        """Generates the configured number of folds."""
        groups = np.array([f"s{i}" for i in range(50)])
        splits = generate_splits(sample_config, groups)
        assert len(splits) == sample_config.split.n_splits

    def test_no_subject_in_multiple_folds(self, sample_config):
        """No subject appears in both train and validation of any fold."""
        groups = np.array([f"s{i}" for i in range(50)])
        splits = generate_splits(sample_config, groups)

        for train_idx, val_idx in splits:
            train_subjects = set(groups[train_idx])
            val_subjects = set(groups[val_idx])
            overlap = train_subjects & val_subjects
            assert len(overlap) == 0, f"Subject overlap: {overlap}"

    def test_all_indices_covered(self, sample_config):
        """Every sample appears in exactly one validation fold."""
        groups = np.array([f"s{i}" for i in range(50)])
        splits = generate_splits(sample_config, groups)

        all_val_indices = set()
        for _, val_idx in splits:
            all_val_indices.update(val_idx)
        assert all_val_indices == set(range(len(groups)))

    def test_raises_on_unknown_method(self, sample_config):
        """Raises ValueError for unknown split method."""
        from omegaconf import OmegaConf

        bad_config = OmegaConf.create(
            {"split": {"method": "UnknownMethod", "n_splits": 3}}
        )
        groups = np.array([f"s{i}" for i in range(50)])
        with pytest.raises(ValueError, match="Unknown split method"):
            generate_splits(bad_config, groups)


class TestGenerateHoldoutSplit:
    """Tests for holdout split generation."""

    def test_splits_are_disjoint(self):
        """Train and test indices do not overlap."""
        groups = np.array([f"s{i}" for i in range(100)])
        train_idx, test_idx = generate_holdout_split(groups, test_ratio=0.2)
        assert len(set(train_idx) & set(test_idx)) == 0

    def test_approximate_ratio(self):
        """Test set is approximately the requested ratio."""
        groups = np.array([f"s{i}" for i in range(100)])
        train_idx, test_idx = generate_holdout_split(groups, test_ratio=0.2)
        test_ratio = len(test_idx) / (len(train_idx) + len(test_idx))
        assert 0.1 <= test_ratio <= 0.3

    def test_reproducible_with_seed(self):
        """Same seed produces same split."""
        groups = np.array([f"s{i}" for i in range(100)])
        train1, test1 = generate_holdout_split(groups, random_state=42)
        train2, test2 = generate_holdout_split(groups, random_state=42)
        np.testing.assert_array_equal(train1, train2)
        np.testing.assert_array_equal(test1, test2)

    def test_no_subject_in_both_splits(self):
        """No subject appears in both train and test."""
        # Create groups with repeated subjects
        groups = np.array(["s0", "s0", "s1", "s1", "s2", "s2", "s3", "s3"])
        train_idx, test_idx = generate_holdout_split(groups, test_ratio=0.3)
        train_subjects = set(groups[train_idx])
        test_subjects = set(groups[test_idx])
        assert len(train_subjects & test_subjects) == 0


class TestSaveSplitIndex:
    """Tests for split index saving."""

    def test_saves_json_file(self, tmp_output_dir):
        """Split index is saved as JSON."""
        groups = np.array(["s0", "s1", "s2", "s3"])
        splits = [(np.array([0, 1]), np.array([2, 3]))]
        output_path = str(tmp_output_dir / "split_index.json")

        path = save_split_index(groups, splits, output_path=output_path)
        assert path.exists()
