"""Tests for holdout_trainer -- hold-out model training."""

import numpy as np
import polars as pl
import pytest

from src.models.holdout_trainer import HoldoutResult, train_holdout_model


@pytest.fixture
def synthetic_data_with_holdout() -> tuple[pl.DataFrame, dict[str, int]]:
    """Create synthetic ECG data and a holdout split."""
    rng = np.random.default_rng(42)
    n_subjects = 50

    af_labels = np.array([1] * 15 + [0] * 35)
    rng.shuffle(af_labels)

    record_ids = []
    af_expanded = []
    features = {f"feat_{i}": [] for i in range(10)}

    for i, af in enumerate(af_labels):
        for _ in range(2):
            record_ids.append(f"r{i}")
            af_expanded.append(af)
            for j in range(10):
                features[f"feat_{j}"].append(af * 0.5 + rng.normal(0, 0.3))

    data = {"record_id": record_ids, "af_label": af_expanded}
    data.update(features)
    df = pl.DataFrame(data)

    # 80/20 split
    holdout_split = {}
    for i in range(n_subjects):
        holdout_split[f"r{i}"] = 1 if i < 10 else 0

    return df, holdout_split


class TestTrainHoldoutModel:
    def test_returns_holdout_result(
        self, synthetic_data_with_holdout: tuple[pl.DataFrame, dict[str, int]]
    ) -> None:
        df, holdout_split = synthetic_data_with_holdout
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_holdout_model(
            feature_matrix=df,
            holdout_split=holdout_split,
            feature_cols=feature_cols,
        )
        assert isinstance(result, HoldoutResult)

    def test_holdout_predictions_only_holdout_subjects(
        self, synthetic_data_with_holdout: tuple[pl.DataFrame, dict[str, int]]
    ) -> None:
        df, holdout_split = synthetic_data_with_holdout
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_holdout_model(
            feature_matrix=df,
            holdout_split=holdout_split,
            feature_cols=feature_cols,
        )
        holdout_subjects = {k for k, v in holdout_split.items() if v == 1}
        pred_subjects = set(result.holdout_predictions["record_id"].unique().to_list())
        assert pred_subjects <= holdout_subjects

    def test_train_and_holdout_counts(
        self, synthetic_data_with_holdout: tuple[pl.DataFrame, dict[str, int]]
    ) -> None:
        df, holdout_split = synthetic_data_with_holdout
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_holdout_model(
            feature_matrix=df,
            holdout_split=holdout_split,
            feature_cols=feature_cols,
        )
        assert result.n_train_samples > 0
        assert result.n_holdout_samples > 0
        assert result.n_train_subjects > 0
        assert result.n_holdout_subjects > 0

    def test_logistic_regression_model(
        self, synthetic_data_with_holdout: tuple[pl.DataFrame, dict[str, int]]
    ) -> None:
        df, holdout_split = synthetic_data_with_holdout
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_holdout_model(
            feature_matrix=df,
            holdout_split=holdout_split,
            feature_cols=feature_cols,
            model_type="logistic_regression",
        )
        assert result.model_name == "logistic_regression"

    def test_unsupported_model_raises(
        self, synthetic_data_with_holdout: tuple[pl.DataFrame, dict[str, int]]
    ) -> None:
        df, holdout_split = synthetic_data_with_holdout
        feature_cols = [f"feat_{i}" for i in range(10)]
        with pytest.raises(ValueError, match="Unsupported model_type"):
            train_holdout_model(
                feature_matrix=df,
                holdout_split=holdout_split,
                feature_cols=feature_cols,
                model_type="random_forest",
            )

    def test_predictions_have_probability_range(
        self, synthetic_data_with_holdout: tuple[pl.DataFrame, dict[str, int]]
    ) -> None:
        df, holdout_split = synthetic_data_with_holdout
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_holdout_model(
            feature_matrix=df,
            holdout_split=holdout_split,
            feature_cols=feature_cols,
        )
        probs = result.holdout_predictions["af_prob_pred"].to_numpy()
        assert np.all(probs >= 0.0)
        assert np.all(probs <= 1.0)
