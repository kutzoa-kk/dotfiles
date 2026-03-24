# Data Split Policy -- AFib Classification

## Split Unit

**record_id** -- All data from the same subject must reside in the same split.

## Grouping Constraints

- **Multi-record co-location**: If a subject has multiple ECG recordings, ALL recordings
  must be placed in the same fold/split.
- Violating this constraint constitutes data leakage and invalidates all results.

## Cross-Validation Strategy

- **Method**: StratifiedGroupKFold
- **Fold count**: 5
- **Group key**: `record_id` (all records from same subject in same fold)
- **Stratification**: `af_label` (maintain AF prevalence ratio across folds)
- **Seed**: 42

## Hold-out Evaluation

- **Method**: Random stratified group hold-out (80% train / 20% hold-out)
- **Stratification**: `af_label` (maintain AF prevalence in both sets)
- **Group key**: `record_id` (subject-level split)
- **Seed**: 123

## Split Artifacts

Split assignments saved to:
- `data/processed/split_index.json` -- record_id -> fold mapping (CV)
- `data/processed/holdout_split.json` -- record_id -> split (0=train, 1=holdout)

These serve as audit artifacts for reproducibility.

## Split Validation

After every split generation, run:
```bash
python src/schema/leakage_check.py \
    --schema src/schema/feature_availability.yaml \
    --features data/processed/feature_matrix.parquet \
    --split data/processed/split_index.json \
    --subject-col record_id
```

Validates:
- No subject appears in multiple splits
- Intra-subject data is co-located in same fold
- Feature matrix contains only inference_available variables
