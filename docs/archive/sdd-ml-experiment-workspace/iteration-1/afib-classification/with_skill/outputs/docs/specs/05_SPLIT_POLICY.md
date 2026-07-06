# Split Policy -- afib-classification

## Split Unit

**Group key**: `record_id`

All data from the same ECG recording must remain in the same fold during cross-validation and in the same partition during holdout splitting. This prevents information leakage from correlated observations.

## Cross-Validation Strategy

- **Method**: StratifiedGroupKFold
- **Folds**: 5
- **Stratification**: By `af_label` (ensures class balance across folds)
- **Grouping**: By `record_id` (prevents group leakage)
- **Shuffle**: True (with fixed random seed for reproducibility)

### Validation Requirements

1. No `record_id` appears in both train and validation within any fold
2. Class distribution is approximately balanced across folds
3. All samples appear in exactly one validation fold

## Holdout Strategy

- **Method**: Random group-aware split (GroupShuffleSplit)
- **Split ratio**: 80% train / 20% test
- **Random state**: Same as experiment seed (42)
- **Grouping**: By `record_id`

### Holdout Protocol

1. Holdout split is generated ONCE and locked
2. Phase B CV operates ONLY on the 80% training partition
3. Phase C evaluates ONCE on the 20% holdout partition
4. Re-evaluation on holdout after seeing results is PROHIBITED

## Integrity Checks

Before any training:
- Verify no group overlap between train and validation (per fold)
- Verify no group overlap between train and holdout partitions
- Log class distribution per fold/partition
- Save split assignments to `data/processed/split_index.json` for audit
