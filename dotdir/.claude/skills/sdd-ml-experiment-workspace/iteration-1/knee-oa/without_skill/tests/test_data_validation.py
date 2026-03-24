"""Tests for data validation schema."""

import pandas as pd
import pytest

from src.schema.data_validation import (
    validate_kl_grade_distribution,
)


@pytest.fixture
def valid_metadata() -> pd.DataFrame:
    """Valid clinical metadata sample."""
    return pd.DataFrame(
        {
            "patient_id": [f"P{i:03d}" for i in range(20)],
            "sex": ["M"] * 10 + ["F"] * 10,
            "age": [55.0 + i for i in range(20)],
            "side": (["L", "R"] * 10),
            "kl_grade": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4] * 2,
            "visit_date": ["2023-01-15"] * 20,
        }
    )


class TestKLGradeDistribution:
    def test_returns_dict(self, valid_metadata: pd.DataFrame) -> None:
        result = validate_kl_grade_distribution(valid_metadata)
        assert isinstance(result, dict)

    def test_contains_grade_counts(self, valid_metadata: pd.DataFrame) -> None:
        result = validate_kl_grade_distribution(valid_metadata)
        assert "grade_distribution" in result
        assert "total_samples" in result

    def test_min_samples_check(self, valid_metadata: pd.DataFrame) -> None:
        result = validate_kl_grade_distribution(valid_metadata)
        assert "min_samples_met" in result

    def test_class_balance_check(self, valid_metadata: pd.DataFrame) -> None:
        result = validate_kl_grade_distribution(valid_metadata)
        assert "class_balance_met" in result
        # Equal distribution = balanced
        assert result["class_balance_met"] is True

    def test_imbalanced_data_detected(self) -> None:
        """Detect class imbalance when one grade dominates."""
        df = pd.DataFrame(
            {
                "kl_grade": [0] * 80 + [1] * 5 + [2] * 5 + [3] * 5 + [4] * 5,
            }
        )
        result = validate_kl_grade_distribution(df)
        assert result["class_balance_met"] is False
