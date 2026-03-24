"""Tests for split generator."""

import numpy as np
import polars as pl
import pytest

from src.split_generator import generate_splits, generate_temporal_holdout


class TestGenerateSplits:
    """Tests for CV split generation."""

    def test_correct_number_of_folds(self, sample_config):
        """Generates the configured number of folds."""
        groups = np.array([f"PAT_{i:03d}" for i in range(50)])
        splits = generate_splits(sample_config, groups)
        assert len(splits) == sample_config.split.n_splits

    def test_no_subject_in_multiple_folds(self, sample_config):
        """No subject appears in both train and validation of any fold."""
        # Simulate patients with L/R knees
        patient_ids = []
        for i in range(25):
            patient_ids.extend([f"PAT_{i:03d}"] * 2)  # L and R
        groups = np.array(patient_ids)

        splits = generate_splits(sample_config, groups)

        for train_idx, val_idx in splits:
            train_subjects = set(groups[train_idx])
            val_subjects = set(groups[val_idx])
            overlap = train_subjects & val_subjects
            assert len(overlap) == 0, f"Subject overlap: {overlap}"

    def test_all_indices_covered(self, sample_config):
        """Every sample appears in exactly one validation fold."""
        groups = np.array([f"PAT_{i:03d}" for i in range(50)])
        splits = generate_splits(sample_config, groups)

        all_val_indices = set()
        for _, val_idx in splits:
            all_val_indices.update(val_idx)
        assert all_val_indices == set(range(len(groups)))

    def test_lr_colocation(self, sample_config):
        """Left and right knees of same patient are in the same fold."""
        patient_ids = []
        sides = []
        for i in range(25):
            patient_ids.extend([f"PAT_{i:03d}", f"PAT_{i:03d}"])
            sides.extend(["L", "R"])
        groups = np.array(patient_ids)

        splits = generate_splits(sample_config, groups)

        for fold_idx, (train_idx, val_idx) in enumerate(splits):
            val_patients = set(groups[val_idx])
            for patient in val_patients:
                # Find all indices for this patient
                patient_indices = np.where(groups == patient)[0]
                # All should be in validation
                for idx in patient_indices:
                    assert idx in val_idx, (
                        f"Patient {patient} has index {idx} in train "
                        f"but other indices in val (fold {fold_idx})"
                    )

    def test_raises_on_unknown_method(self, sample_config):
        """Raises ValueError for unknown split method."""
        from omegaconf import OmegaConf

        cfg = OmegaConf.create({
            "split": {
                "method": "UnknownMethod",
                "n_splits": 3,
                "group_key": "patient_id",
            }
        })
        groups = np.array(["a", "b", "c"])
        with pytest.raises(ValueError, match="Unknown split method"):
            generate_splits(cfg, groups)


class TestGenerateTemporalHoldout:
    """Tests for temporal holdout split."""

    def test_splits_by_date(self):
        """Correctly splits data by cutoff date."""
        from omegaconf import OmegaConf

        df = pl.DataFrame({
            "patient_id": ["P001", "P002", "P003", "P004"],
            "visit_date": ["2023-06-01", "2023-12-01", "2024-03-01", "2024-06-01"],
        })
        cfg = OmegaConf.create({
            "holdout": {"cutoff_date": "2024-01-01"},
        })

        train_idx, test_idx = generate_temporal_holdout(df, cfg)
        assert len(train_idx) == 2  # 2023 visits
        assert len(test_idx) == 2  # 2024 visits

    def test_raises_on_empty_test(self):
        """Raises ValueError if no test samples after cutoff."""
        from omegaconf import OmegaConf

        df = pl.DataFrame({
            "patient_id": ["P001", "P002"],
            "visit_date": ["2022-01-01", "2023-01-01"],
        })
        cfg = OmegaConf.create({
            "holdout": {"cutoff_date": "2025-01-01"},
        })

        with pytest.raises(ValueError, match="No test samples"):
            generate_temporal_holdout(df, cfg)
