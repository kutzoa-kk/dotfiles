# Metrics & Gate Conditions — sarcopenia-risk-prediction

## Primary Metric

| Metric | Definition | Rationale |
|--------|-----------|-----------|
| Spearman rho | Rank correlation between predicted and actual sarcopenia risk score | Captures monotonic relationship without assuming linearity; robust to outliers |

## Secondary Metrics

| Metric | Definition | Purpose |
|--------|-----------|---------|
| RMSE | Root Mean Squared Error | Measures prediction magnitude error |
| MAE | Mean Absolute Error | Robust central tendency of error |

## Phase Gate Conditions

### Phase A -> Phase B
| Gate | Metric | Threshold | Operator |
|------|--------|-----------|----------|
| Score validity | Spearman rho (score vs clinical correlate) | 0.5 | >= |

**On failure**: Revise score construction. Do NOT proceed to Phase B.

### Phase B -> Phase C
| Gate | Metric | Threshold | Operator |
|------|--------|-----------|----------|
| Prediction quality | Spearman rho (OOF predictions vs actual) | 0.3 | >= |

**On failure**: Return to feature engineering / model tuning. Do NOT evaluate on holdout.

### Phase C (Holdout)
| Gate | Metric | Threshold | Protocol |
|------|--------|-----------|----------|
| Generalization | Spearman rho (holdout predictions vs actual) | Report only | ONE-SHOT |

**Protocol**: Phase C is ONE-SHOT. Results are reported regardless of pass/fail. Do NOT re-tune and re-evaluate.

## Multiple Comparison Correction

If testing more than one hypothesis, apply Bonferroni correction or report all p-values alongside uncorrected results.
