# Schema Templates

## feature_availability.yaml

Generate at `src/schema/feature_availability.yaml`. Replace lists with interview answers.

```yaml
# Feature Availability Schema
# Variables classified by inference-time availability.
# AI agents MUST NOT use inference_unavailable features for model training.

features:
  # Features available at inference time — safe to use as model inputs
  inference_available:
    # {{features_available_list — one per line, YAML list format}}
    - example_feature_1
    - example_feature_2

  # Features NOT available at inference time — PROHIBITED as training features
  # Using these causes target leakage and invalidates the model.
  inference_unavailable:
    # {{features_unavailable_list}}
    - target_label
    - post_hoc_score

  # Auxiliary targets for multi-task learning — NOT usable as input features
  auxiliary_targets:
    # {{auxiliary_targets_list — empty list [] if none}}
    []
```

## data_validation.py (Pandera)

Generate at `src/schema/data_validation.py`. Adapt checks to data modality.

### Tabular Data Template

```python
"""Data validation schema using Pandera.

Run before any data processing:
    python -m src.schema.data_validation --input data/processed/dataset.parquet
"""

import argparse
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Column, Check, DataFrameSchema


dataset_schema = DataFrameSchema(
    columns={
        # Subject identifier — must be non-null, used for split grouping
        "{{subject_id_field}}": Column(
            str,
            Check.str_length(min_value=1),
            nullable=False,
            description="Primary subject identifier for split grouping",
        ),
        # {{Add columns per interview answers. Examples below.}}
        # "sex": Column(int, Check.isin([0, 1]), nullable=False),
        # "height": Column(float, Check.in_range(100, 250), nullable=True),
        # "weight": Column(float, Check.in_range(20, 300), nullable=True),
    },
    # Uniqueness constraint: each (subject, session, side) combo is unique
    # unique=["{{subject_id_field}}", "session_id", "side"],
    coerce=True,
    strict="filter",  # warn on extra columns
)


def validate(filepath: Path) -> pd.DataFrame:
    """Load and validate a dataset file. Raise on schema violation."""
    df = pd.read_parquet(filepath)
    validated = dataset_schema.validate(df, lazy=True)
    print(f"Validation passed: {len(validated)} rows, {len(validated.columns)} columns")
    return validated


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dataset schema")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")
    validate(args.input)


if __name__ == "__main__":
    main()
```

### Time-Series / Sensor Data Additions

If data modality includes time-series, add these checks:

```python
        # Sampling rate check (expected: {{sampling_rate}} Hz)
        # "timestamp": Column(float, Check(
        #     lambda s: s.diff().dropna().between(
        #         1/{{sampling_rate}} * 0.95,
        #         1/{{sampling_rate}} * 1.05
        #     ).all(),
        #     error="Sampling interval deviates >5% from {{sampling_rate}}Hz"
        # )),

        # Zero-value semantics: {{zero_semantics}}
        # If "non-contact": zeros are valid
        # If "missing": add Check(lambda s: (s != 0).all())
        # If "both": add a separate is_contact flag column
```
