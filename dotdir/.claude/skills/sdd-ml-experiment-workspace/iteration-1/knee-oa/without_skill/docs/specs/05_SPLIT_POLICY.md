# Split Policy -- Knee OA Progression

## Principles

1. **Patient-level splitting**: `patient_id` is the split unit. All observations from the same patient must reside in the same fold/split.
2. **Side co-location**: L/R knee data from the same patient are automatically co-located because splitting is at the patient level.
3. **No data leakage**: Train/test separation must be strict. No patient appears in both sets.

## Cross-Validation (Phase B)

- **Method**: GroupKFold (sklearn)
- **n_splits**: 5
- **Group key**: `patient_id`
- **Side co-location**: Automatic (patient-level grouping)
- **Seed**: 42 (for reproducible shuffling)

```
GroupKFold ensures:
- Each patient_id appears in exactly ONE test fold
- L/R sides of the same patient are always in the same fold
- No patient-level data leakage across folds
```

## Temporal Holdout (Phase C)

- **Method**: Temporal split by `visit_date`
- **Cutoff**: year < 2024 = train, year >= 2024 = holdout
- **Patient assignment**: Based on MAXIMUM visit year per patient
  - If ANY visit is >= 2024, patient goes to holdout
  - Only patients with ALL visits < 2024 go to train

```
Temporal split ensures:
- No future data leakage into training
- Model evaluated on truly unseen time period
- Simulates real-world deployment scenario
```

## Validation Checks

Before any training:
1. Run `src/schema/leakage_check.py` to verify no forbidden features
2. Run `src/split_generator.validate_split_integrity()` to verify:
   - All patients assigned to exactly one fold
   - No patient appears in multiple folds
   - L/R sides are co-located
3. For Phase C: verify temporal integrity (no patient in both train and holdout)

## Preprocessing Within Folds

**CRITICAL**: All preprocessing (StandardScaler, Imputer, etc.) must be fit INSIDE each CV fold using only training data.

```
WRONG:  scaler.fit(all_data) -> scaler.transform(train) + scaler.transform(test)
RIGHT:  scaler.fit(train_fold) -> scaler.transform(train_fold) + scaler.transform(test_fold)
```
