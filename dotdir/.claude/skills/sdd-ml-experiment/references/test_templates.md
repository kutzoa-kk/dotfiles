# Test Infrastructure Templates

Generate test files that follow TDD conventions — tests should be written to
guide implementation, not just validate it after the fact.

## pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Root conftest.py

Place at experiment root (same level as `src/` and `tests/`).

```python
"""Root conftest — ensures src is importable from tests."""

import sys
from pathlib import Path

# Add experiment root to Python path so `from src.xxx import yyy` works
sys.path.insert(0, str(Path(__file__).parent))
```

## tests/conftest.py — Shared Fixtures

```python
"""Shared test fixtures for {{experiment_name}}.

Provides synthetic datasets, mock configs, and temporary directories.
All fixtures create minimal but realistic data structures.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from omegaconf import DictConfig, OmegaConf


@pytest.fixture
def sample_data() -> pl.DataFrame:
    """Minimal synthetic dataset for testing.

    Contains enough rows and variety to exercise data processing logic
    without being so large that tests are slow.
    """
    np.random.seed(42)
    n = 50

    return pl.DataFrame({
        "{{subject_id_field}}": [f"subj_{i:03d}" for i in range(n)],
        # {{Add columns matching your feature_availability.yaml}}
        # Example:
        # "feature_1": np.random.randn(n).tolist(),
        # "feature_2": np.random.randn(n).tolist(),
        # "target": np.random.randn(n).tolist(),
    })


@pytest.fixture
def sample_config() -> DictConfig:
    """Minimal Hydra-compatible config for testing.

    Mirrors the structure of conf/config.yaml but with test-appropriate values.
    """
    return OmegaConf.create({
        "project_name": "test_experiment",
        "seed": 42,
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "schema_path": "src/schema/feature_availability.yaml",
        },
        "model": {
            "name": "baseline",
            "type": "lightgbm",
            "params": {
                "n_estimators": 10,  # Small for fast tests
                "learning_rate": 0.1,
                "max_depth": 3,
                "random_state": 42,
            },
        },
        "split": {
            "method": "GroupKFold",
            "n_splits": 3,  # Small for fast tests
            "group_key": "{{subject_id_field}}",
        },
        "gates": {
            "phase_a": {
                # {{gate conditions}}
            },
            "phase_b": {
                # {{gate conditions}}
            },
        },
    })


@pytest.fixture
def tmp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def feature_schema() -> dict:
    """Feature availability schema for testing."""
    return {
        "features": {
            "inference_available": [
                # {{test features}}
            ],
            "inference_unavailable": [
                # {{leak candidates}}
            ],
            "auxiliary_targets": [],
        }
    }


@pytest.fixture
def feature_schema_path(tmp_output_dir, feature_schema) -> Path:
    """Write feature schema to temp file and return path."""
    import yaml

    path = tmp_output_dir / "feature_availability.yaml"
    with open(path, "w") as f:
        yaml.dump(feature_schema, f)
    return path
```

## Test Stub Pattern

For each `src/**/*.py` module, generate a corresponding test file.

### test_feature_matrix_builder.py

```python
"""Tests for feature matrix builder."""

import polars as pl
import pytest

from src.features.feature_matrix_builder import build_feature_matrix


class TestBuildFeatureMatrix:
    """Tests for the build_feature_matrix function."""

    def test_returns_three_components(self, sample_config):
        """Feature matrix builder returns (features, target, groups)."""
        # This test guides implementation: the function must return a 3-tuple
        features, target, groups = build_feature_matrix(sample_config)
        assert isinstance(features, (pl.DataFrame, object))
        assert target is not None
        assert groups is not None

    def test_excludes_unavailable_features(self, sample_config):
        """No inference_unavailable features appear in the matrix."""
        features, _, _ = build_feature_matrix(sample_config)
        # {{Assert no leaked columns are present}}

    def test_preserves_row_count(self, sample_config):
        """Feature count matches expected after filtering."""
        features, target, groups = build_feature_matrix(sample_config)
        assert len(features) == len(target)
        assert len(features) == len(groups)
```

### test_phase_a_evaluator.py

```python
"""Tests for Phase A evaluator."""

import pytest

from src.models.phase_a_evaluator import run_phase_a_evaluation


class TestPhaseAEvaluation:
    """Tests for Phase A validation."""

    def test_returns_phase_result(self, sample_config):
        """Phase A returns a result with metrics and gates."""
        result = run_phase_a_evaluation(sample_config)
        assert hasattr(result, "metrics")
        assert hasattr(result, "gates")
        assert hasattr(result, "all_gates_passed")

    def test_metrics_are_numeric(self, sample_config):
        """All metrics are float values."""
        result = run_phase_a_evaluation(sample_config)
        for name, value in result.metrics.items():
            assert isinstance(value, (int, float)), f"{name} is not numeric"

    def test_gates_are_boolean(self, sample_config):
        """All gate values are boolean."""
        result = run_phase_a_evaluation(sample_config)
        for name, value in result.gates.items():
            assert isinstance(value, bool), f"{name} is not boolean"
```

### test_split_generator.py

```python
"""Tests for split generator."""

import numpy as np
import pytest

from src.split_generator import generate_splits


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
```

## Naming Convention

| Source Module | Test File |
|---|---|
| `src/features/feature_matrix_builder.py` | `tests/test_feature_matrix_builder.py` |
| `src/models/phase_a_evaluator.py` | `tests/test_phase_a_evaluator.py` |
| `src/models/direction_trainer.py` | `tests/test_direction_trainer.py` |
| `src/split_generator.py` | `tests/test_split_generator.py` |
| `src/data_access.py` | `tests/test_data_access.py` |
