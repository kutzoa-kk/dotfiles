# Split Policy — sarcopenia-risk-prediction

## Subject-Level Splitting

- **Split unit**: `username`
- **Constraint**: All observations from the same subject MUST reside in the same fold/partition
- **Rationale**: Prevents optimistic bias from seeing the same subject in both train and validation

## Cross-Validation (Phase B)

| Parameter | Value |
|-----------|-------|
| Method | GroupKFold |
| Folds | 5 |
| Group key | username |
| Stratification | None (continuous target) |

## Holdout (Phase C)

| Parameter | Value |
|-----------|-------|
| Method | Random subject-level split |
| Train ratio | 80% of unique subjects |
| Test ratio | 20% of unique subjects |
| Random seed | 42 |
| Protocol | ONE-SHOT |

## Holdout Protocol

1. The holdout split is generated ONCE using seed=42
2. The holdout set is NEVER used for model development
3. Phase C evaluation runs AT MOST ONCE
4. Results are reported regardless of outcome
5. If holdout fails, return to Phase B CV — do NOT re-split or re-evaluate

## Validation Checks

Before training:
- [ ] No subject appears in both train and validation of any fold
- [ ] Holdout subjects are disjoint from training subjects
- [ ] Split is reproducible (same seed produces same split)
- [ ] All subjects appear in exactly one validation fold
