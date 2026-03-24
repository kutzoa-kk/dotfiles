# Hypotheses — knee-oa-progression

> Pre-registered hypotheses for knee OA progression prediction from joint angle time-series.

## Primary Hypothesis

**H1**: Knee joint angle time-series features (derived from 100 Hz motion capture data) can predict KL grade (0-4) with RMSE <= 1.0 using ordinal regression models (LightGBM, XGBoost).

**Rationale**: OA progression affects joint biomechanics measurably. Knee flexion range, varus/valgus alignment, and gait cycle parameters are expected to correlate with structural severity as assessed by KL grading.

## Secondary Hypotheses

**H2**: At least one biomechanical biomarker group (knee angle features or gait cycle features) will show Spearman rho >= 0.4 with KL grade.

**Rationale**: Prior literature suggests that gait abnormalities increase with OA severity. Phase A validates this assumption before building prediction models.

**H3**: The prediction model generalizes to temporally held-out data (visit_date >= 2024), achieving RMSE <= 1.2 on the holdout set.

**Rationale**: Temporal stability indicates the relationship between biomechanics and KL grade is consistent over time and not an artifact of measurement drift.

## Analysis Plan

1. **Phase A**: Compute Spearman correlations between KL grade and all biomarker features. Gate: rho >= 0.4 for at least one biomarker group.
2. **Phase B**: Train LightGBM and XGBoost with GroupKFold 5-fold CV. Feature selection via Nested CV RFE. Gate: RMSE <= 1.0.
3. **Phase C**: One-shot holdout evaluation on temporal split (< 2024 vs >= 2024).

## Post-Hoc Analysis (Exploratory)

Any findings not pre-registered above must be labeled as "exploratory" and should be validated on a separate partition. These include:
- Subgroup analysis by sex or age group
- Non-linear feature interactions
- Side-specific (L/R) prediction differences
