# Metrics & Gate Conditions — knee-oa-progression

## Primary Metrics

| Metric | Description | Library |
|--------|-------------|---------|
| RMSE | Root Mean Squared Error of KL grade prediction | `sklearn.metrics.mean_squared_error` |
| MAE | Mean Absolute Error of KL grade prediction | `sklearn.metrics.mean_absolute_error` |
| Ordinal Accuracy (within 1) | Fraction of predictions within 1 grade of truth | Custom |
| Exact Accuracy | Fraction of exact grade matches | Custom |
| Spearman rho | Rank correlation between features and KL grade | `scipy.stats.spearmanr` |

## Phase Gate Conditions

### Phase A -> Phase B

| Gate | Metric | Threshold | Operator | Rationale |
|------|--------|-----------|----------|-----------|
| Biomarker correlation | Spearman rho (best biomarker vs KL grade) | 0.4 | >= | Validates that biomechanical features carry signal about OA severity |

**Failure action**: Re-examine biomarker definitions, data quality, and feature engineering. Do NOT proceed to Phase B.

### Phase B -> Phase C

| Gate | Metric | Threshold | Operator | Rationale |
|------|--------|-----------|----------|-----------|
| CV prediction quality | RMSE (cross-validated) | 1.0 | <= | KL grade is 0-4; RMSE > 1.0 means average error exceeds one grade level |

**Failure action**: Diagnose model, features, or data issues. Return to CV. Do NOT evaluate on holdout.

### Phase C (Holdout)

| Gate | Metric | Threshold | Operator | Rationale |
|------|--------|-----------|----------|-----------|
| Holdout RMSE | RMSE on temporal holdout | 1.2 | <= | Relaxed threshold for generalization; informational |

**Note**: Phase C is ONE-SHOT. Results are reported regardless of gate status. No re-tuning allowed.

## Reporting Requirements

All reports must include:
- Total number of experimental runs attempted
- All run results in a summary table
- Per-fold metrics for Phase B (not just aggregates)
- Confidence intervals for Phase C holdout metrics
- Feature importance rankings
