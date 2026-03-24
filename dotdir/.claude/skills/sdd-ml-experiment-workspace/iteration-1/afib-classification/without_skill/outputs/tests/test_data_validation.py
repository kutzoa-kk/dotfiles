"""Tests for data validation schema."""

import pandas as pd
import pytest

from src.schema.data_validation import ecg_dataset_schema


class TestECGDatasetSchema:
    def test_valid_data_passes(self) -> None:
        df = pd.DataFrame(
            {
                "record_id": ["r1", "r2", "r3"],
                "af_label": [0, 1, 0],
                "rr_mean": [800.0, 600.0, 750.0],
                "rr_std": [50.0, 120.0, 40.0],
                "rr_rmssd": [30.0, 90.0, 25.0],
                "heart_rate_mean": [75.0, 100.0, 80.0],
            }
        )
        validated = ecg_dataset_schema.validate(df, lazy=True)
        assert len(validated) == 3

    def test_invalid_af_label_fails(self) -> None:
        df = pd.DataFrame(
            {
                "record_id": ["r1"],
                "af_label": [2],  # Invalid: not 0 or 1
                "rr_mean": [800.0],
                "rr_std": [50.0],
                "rr_rmssd": [30.0],
                "heart_rate_mean": [75.0],
            }
        )
        with pytest.raises(Exception):
            ecg_dataset_schema.validate(df, lazy=True)

    def test_missing_record_id_fails(self) -> None:
        df = pd.DataFrame(
            {
                "record_id": [None],
                "af_label": [0],
                "rr_mean": [800.0],
                "rr_std": [50.0],
                "rr_rmssd": [30.0],
                "heart_rate_mean": [75.0],
            }
        )
        with pytest.raises(Exception):
            ecg_dataset_schema.validate(df, lazy=True)

    def test_out_of_range_heart_rate_fails(self) -> None:
        df = pd.DataFrame(
            {
                "record_id": ["r1"],
                "af_label": [0],
                "rr_mean": [800.0],
                "rr_std": [50.0],
                "rr_rmssd": [30.0],
                "heart_rate_mean": [500.0],  # Invalid: > 300
            }
        )
        with pytest.raises(Exception):
            ecg_dataset_schema.validate(df, lazy=True)
