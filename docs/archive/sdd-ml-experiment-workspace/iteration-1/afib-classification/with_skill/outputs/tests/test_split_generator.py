"""Tests for split generator."""

import numpy as np
import pytest

from src.split_generator import generate_cv_splits, generate_holdout_split


class TestGenerateCVSplits:
    """Tests for CV split generation."""

    def test_correct_number_of_folds(self, sample_config):
        """Generates the configured number of folds."""
        groups = np.array([f"rec_{i:03d}" for i in range(50)])
        y = np.random.choice([0, 1], 50, p=[0.7, 0.3])
        splits = generate_cv_splits(sample_config, y, groups)
        assert len(splits) == sample_config.split.n_splits

    def test_no_group_in_multiple_folds(self, sample_config):
        """No group appears in both train and validation of any fold."""
        groups = np.array([f"rec_{i:03d}" for i in range(50)])
        y = np.random.choice([0, 1], 50, p=[0.7, 0.3])
        splits = generate_cv_splits(sample_config, y, groups)

        for train_idx, val_idx in splits:
            train_groups = set(groups[train_idx])
            val_groups = set(groups[val_idx])
            overlap = train_groups & val_groups
            assert len(overlap) == 0, f"Group overlap: {overlap}"

    def test_all_indices_covered(self, sample_config):
        """Every sample appears in exactly one validation fold."""
        groups = np.array([f"rec_{i:03d}" for i in range(50)])
        y = np.random.choice([0, 1], 50, p=[0.7, 0.3])
        splits = generate_cv_splits(sample_config, y, groups)

        all_val_indices = set()
        for _, val_idx in splits:
            all_val_indices.update(val_idx)
        assert all_val_indices == set(range(len(groups)))


class TestGenerateHoldoutSplit:
    """Tests for holdout split generation."""

    def test_returns_two_arrays(self, sample_config):
        """Holdout split returns train and test index arrays."""
        groups = np.array([f"rec_{i:03d}" for i in range(50)])
        train_idx, test_idx = generate_holdout_split(sample_config, groups)
        assert isinstance(train_idx, np.ndarray)
        assert isinstance(test_idx, np.ndarray)

    def test_no_group_overlap(self, sample_config):
        """No group appears in both train and test."""
        groups = np.array([f"rec_{i:03d}" for i in range(50)])
        train_idx, test_idx = generate_holdout_split(sample_config, groups)

        train_groups = set(groups[train_idx])
        test_groups = set(groups[test_idx])
        assert len(train_groups & test_groups) == 0

    def test_approximate_split_ratio(self, sample_config):
        """Test set is approximately 20% of total data."""
        groups = np.array([f"rec_{i:03d}" for i in range(100)])
        train_idx, test_idx = generate_holdout_split(sample_config, groups)

        test_ratio = len(test_idx) / (len(train_idx) + len(test_idx))
        assert 0.10 <= test_ratio <= 0.30  # Allow some tolerance
