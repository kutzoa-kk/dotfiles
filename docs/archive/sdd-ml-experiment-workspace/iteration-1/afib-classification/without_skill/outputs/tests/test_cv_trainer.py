"""Tests for cv_trainer -- LightGBM and Logistic Regression CV training."""

import numpy as np
import polars as pl
import pytest

from src.models.cv_trainer import (
    DEFAULT_LGBM_PARAMS,
    DEFAULT_LR_PARAMS,
    CVTrainingResult,
    FoldResult,
    train_cv_model,
)


@pytest.fixture
def synthetic_ecg_data() -> pl.DataFrame:
    """Create synthetic ECG dataset with known AF signal."""
    rng = np.random.default_rng(42)
    n_subjects = 50
    records_per_subject = 2
    n_total = n_subjects * records_per_subject

    # 30% AF prevalence
    af_labels = np.array([1] * 15 + [0] * 35)
    rng.shuffle(af_labels)

    record_ids = []
    af_labels_expanded = []
    features = {f"feat_{i}": [] for i in range(10)}

    for i, (af) in enumerate(af_labels):
        for _ in range(records_per_subject):
            record_ids.append(f"r{i}")
            af_labels_expanded.append(af)
            for j in range(10):
                # Features correlated with AF label
                base = af * 0.5 + rng.normal(0, 0.3)
                features[f"feat_{j}"].append(base)

    data = {
        "record_id": record_ids,
        "af_label": af_labels_expanded,
    }
    data.update(features)

    return pl.DataFrame(data)


@pytest.fixture
def split_index(synthetic_ecg_data: pl.DataFrame) -> dict[str, int]:
    """Generate split index for synthetic data."""
    from src.split_generator import generate_split_index
    return generate_split_index(synthetic_ecg_data, n_splits=5, seed=42)


class TestTrainCVModel:
    def test_lightgbm_returns_cv_result(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_cv_model(
            feature_matrix=synthetic_ecg_data,
            split_index=split_index,
            feature_cols=feature_cols,
            model_type="lightgbm",
        )
        assert isinstance(result, CVTrainingResult)
        assert result.model_name == "lightgbm"

    def test_logistic_regression_returns_cv_result(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_cv_model(
            feature_matrix=synthetic_ecg_data,
            split_index=split_index,
            feature_cols=feature_cols,
            model_type="logistic_regression",
        )
        assert isinstance(result, CVTrainingResult)
        assert result.model_name == "logistic_regression"

    def test_five_folds_produced(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_cv_model(
            feature_matrix=synthetic_ecg_data,
            split_index=split_index,
            feature_cols=feature_cols,
        )
        assert len(result.fold_results) == 5

    def test_oof_predictions_cover_all_samples(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_cv_model(
            feature_matrix=synthetic_ecg_data,
            split_index=split_index,
            feature_cols=feature_cols,
        )
        # OOF predictions should cover all subjects in split
        available = set(split_index.keys())
        filtered = synthetic_ecg_data.filter(
            pl.col("record_id").cast(pl.Utf8).is_in(list(available))
        )
        assert result.oof_predictions.shape[0] == filtered.shape[0]

    def test_pr_auc_between_0_and_1(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_cv_model(
            feature_matrix=synthetic_ecg_data,
            split_index=split_index,
            feature_cols=feature_cols,
        )
        assert 0.0 <= result.pooled_pr_auc <= 1.0
        assert 0.0 <= result.pooled_roc_auc <= 1.0

    def test_unsupported_model_type_raises(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        with pytest.raises(ValueError, match="Unsupported model_type"):
            train_cv_model(
                feature_matrix=synthetic_ecg_data,
                split_index=split_index,
                feature_cols=feature_cols,
                model_type="random_forest",
            )

    def test_fold_result_has_positive_counts(
        self, synthetic_ecg_data: pl.DataFrame, split_index: dict[str, int]
    ) -> None:
        feature_cols = [f"feat_{i}" for i in range(10)]
        result = train_cv_model(
            feature_matrix=synthetic_ecg_data,
            split_index=split_index,
            feature_cols=feature_cols,
        )
        for fr in result.fold_results:
            assert fr.n_train > 0
            assert fr.n_test > 0
            assert isinstance(fr.n_positive_train, int)
            assert isinstance(fr.n_positive_test, int)


class TestDefaultParams:
    def test_lgbm_params_binary(self) -> None:
        assert DEFAULT_LGBM_PARAMS["objective"] == "binary"

    def test_lr_params_l2(self) -> None:
        assert DEFAULT_LR_PARAMS["penalty"] == "l2"

    def test_lgbm_params_has_random_state(self) -> None:
        assert "random_state" in DEFAULT_LGBM_PARAMS

    def test_lr_params_has_random_state(self) -> None:
        assert "random_state" in DEFAULT_LR_PARAMS
