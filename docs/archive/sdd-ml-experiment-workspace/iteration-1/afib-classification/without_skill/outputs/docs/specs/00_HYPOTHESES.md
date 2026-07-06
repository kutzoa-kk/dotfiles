# Pre-Registered Hypotheses -- AFib Classification

> This document MUST be written BEFORE model training or exploratory analysis.
> Any post-experiment changes require version-controlled justification.

## Primary Hypothesis

**H1**: ECG-derived features (RR intervals, P-wave morphology, QRS complex features,
and heart rate variability measures) can discriminate atrial fibrillation (AF) from
non-AF records with clinically meaningful precision.

- Task type: Binary classification (AF vs non-AF)
- Primary metric: PR-AUC (Precision-Recall Area Under Curve)
- Rationale: PR-AUC is preferred over ROC-AUC for potentially imbalanced clinical datasets
  where the positive class (AF) prevalence may be low.

## Pre-Registered Analysis Plan

### Feature Set

- **Available features**: ECG-derived features only
  - RR interval statistics (mean, std, RMSSD, pNN50, etc.)
  - P-wave morphology features (amplitude, duration, area)
  - QRS complex features (duration, amplitude, axis)
  - Heart rate variability (HRV) features (time-domain and frequency-domain)
- **Prohibited features** (inference_unavailable):
  - `record_id` -- subject identifier
  - `diagnosis_date` -- temporal information causing leakage
  - `af_label` -- target variable
  - `cardiologist_notes` -- text label information

### Models

- **LightGBM**: Gradient boosting classifier with default hyperparameters
- **Logistic Regression**: L2-regularized logistic regression (baseline)

### Evaluation Strategy

| Phase | Description | Gate Condition |
|-------|-------------|----------------|
| A | SKIPPED | AF is a standard diagnostic label |
| B | 5-fold StratifiedGroupKFold CV | PR-AUC >= 0.70 |
| C | Hold-out ONE-SHOT (80/20) | PR-AUC >= 0.65 |

### Statistical Tests

- Number of hypotheses tested: 1 (H1)
- No multiple comparison correction needed for single hypothesis
- Confidence intervals: 95% bootstrap CI for PR-AUC
- Per-fold PR-AUC reported for stability assessment

## Exploratory vs Confirmatory

### Phase B: Confirmatory
- Purpose: Test H1 with pre-specified models and metrics
- Allowed: Train pre-specified models, evaluate with pre-specified metrics
- Forbidden: Changing primary metric, adding models based on intermediate results

### Phase C: Confirmatory (ONE-SHOT)
- Purpose: Final hold-out validation
- Constraint: Evaluate ONCE, report, do NOT iterate
- If gate fails: Return to CV, diagnose failure, re-register hypothesis

### Post-hoc (if applicable)
- All findings labeled as "exploratory"
- Require independent validation

## Deviation Log

| Date | Original Plan | Deviation | Rationale | Approved By |
|------|--------------|-----------|-----------|-------------|
| | | | | |

All deviations from this plan MUST be recorded here before continuing.
