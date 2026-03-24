# Split Policy — knee-oa-progression

## Split Unit

- **Subject ID field**: `patient_id`
- **Grouping constraint**: Left/right knee (`side`) must be co-located with patient.
  Both knees of the same patient always reside in the same fold.

## Cross-Validation (Phase B)

- **Method**: GroupKFold
- **Number of folds**: 5
- **Group key**: `patient_id`
- **Invariant**: No `patient_id` appears in both train and validation of any fold.
- **Co-location**: Since GroupKFold groups by `patient_id`, both L and R sides for
  the same patient are automatically placed in the same fold.

### Validation Checks

Before training, the split generator validates:
1. No group overlap between train and validation sets
2. All indices are covered exactly once across validation folds
3. Both sides (L/R) of each patient are in the same fold

## Holdout Split (Phase C)

- **Method**: Temporal holdout
- **Train**: All data with `visit_date < 2024-01-01`
- **Test**: All data with `visit_date >= 2024-01-01`
- **Protocol**: ONE-SHOT evaluation. No re-tuning after seeing holdout results.

### Temporal Integrity

- Ensures no future data leakage: the model never trains on data from 2024+.
- If a patient has visits both before and after the cutoff, their data may appear
  in both train and test sets. This is acceptable because the model predicts
  disease state at a specific visit, not patient identity.

## Feature Selection

- **Method**: Nested CV RFE (Recursive Feature Elimination)
- Feature selection is performed within the inner loop of CV to prevent
  information leakage from the validation set into feature selection.
- The outer loop evaluates the final model with selected features.

## Audit Trail

- Split assignments are saved to `data/processed/split_index.json`.
- This file maps each `patient_id` to its assigned fold for reproducibility.
- Holdout assignments are derived deterministically from `visit_date`.
