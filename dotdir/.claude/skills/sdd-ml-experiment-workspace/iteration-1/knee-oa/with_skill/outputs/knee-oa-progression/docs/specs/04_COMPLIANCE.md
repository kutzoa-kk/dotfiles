# Compliance Requirements — knee-oa-progression (Medical Level)

> This experiment operates under **medical compliance level**. All requirements below are mandatory.

## 1. Data Handling

### 1.1 Patient Privacy
- All patient identifiers (`patient_id`) must be pseudonymized before analysis.
- Raw data files must be stored in access-controlled directories.
- No patient-identifiable information may appear in logs, reports, or experiment tracking.
- Data must comply with applicable regulations (HIPAA, GDPR, or local equivalent).

### 1.2 Data Provenance
- All data transformations must be logged and reproducible.
- Raw data (`data/raw/`) is read-only; processed data is stored in `data/processed/`.
- A complete audit trail from raw data to final predictions must be maintained.

### 1.3 Data Quality
- Run `src/schema/data_validation.py` before any processing.
- Document any data exclusions with justification.
- Missing data handling must be explicitly documented and clinically justified.

## 2. Model Development

### 2.1 Clinical Validity
- The KL grading system (Kellgren-Lawrence) is a validated clinical standard.
- Model predictions are continuous approximations of ordinal grades and should be interpreted as such.
- Predictions must NOT be used as sole basis for clinical decisions.

### 2.2 Uncertainty Quantification
- All predictions must include confidence intervals or prediction intervals.
- Phase B must report per-fold variance to quantify prediction uncertainty.
- Phase C must report bootstrapped confidence intervals on holdout metrics.

### 2.3 Bias Assessment
- Evaluate model performance stratified by:
  - Sex (male/female)
  - Age group (e.g., <50, 50-65, >65)
  - Knee side (left/right)
  - KL grade subgroup (0-1 vs 2-3 vs 4)
- Document any disparities in prediction accuracy across subgroups.
- If significant disparities exist, recommend mitigation strategies.

### 2.4 Feature Transparency
- Maintain complete feature importance rankings.
- Document which biomechanical features contribute most to predictions.
- Ensure all features are clinically interpretable.

## 3. Experiment Integrity

### 3.1 Pre-Registration
- All hypotheses must be registered in `docs/specs/00_HYPOTHESES.md` before experiments begin.
- Post-hoc findings must be clearly labeled as "exploratory."
- No p-hacking: Phase C holdout is strictly one-shot.

### 3.2 Reproducibility
- All experiments must be reproducible with fixed random seeds.
- Environment dependencies must be version-locked.
- All hyperparameters must be logged in experiment tracking (MLflow).

### 3.3 Anti-Leakage
- Run `src/schema/leakage_check.py` before every training run.
- `radiograph_score` and `kl_grade` must never appear as features.
- Temporal leakage prevention: holdout split strictly by visit_date.
- Patient-level grouping: all data from same patient in same fold.

## 4. Reporting

### 4.1 Full Transparency
- Report ALL experimental runs, including failures.
- Include negative results without suppression.
- Document deviations from pre-registered plan with justification.

### 4.2 Clinical Context
- Frame results in terms of clinical utility (e.g., "average error is less than one KL grade level").
- Compare against inter-rater reliability of KL grading (typically kappa 0.5-0.7).
- Discuss limitations and conditions under which the model should NOT be used.

### 4.3 Required Report Sections
- Study design and data description
- Feature engineering methodology
- Model training and validation methodology
- Results with confidence intervals
- Subgroup analysis
- Limitations and failure modes
- Intended use and contraindications

## 5. Deployment Considerations (Future)

### 5.1 Not for Diagnostic Use
- This model is a research tool, NOT a diagnostic device.
- Any clinical deployment requires regulatory review (FDA 510(k), CE marking, or equivalent).
- Model outputs must be labeled: "Research use only. Not for clinical diagnosis."

### 5.2 Monitoring
- If deployed for research screening, monitor for distribution shift.
- Re-validate periodically on new data cohorts.
- Document model version and training data vintage.

## Compliance Checklist

Before each phase:
- [ ] Data validation passed (`src/schema/data_validation.py`)
- [ ] Leakage check passed (`src/schema/leakage_check.py`)
- [ ] Feature availability schema reviewed
- [ ] Random seeds set and documented

Before Phase C:
- [ ] Phase A and Phase B gates passed
- [ ] No modifications to model after Phase B lock
- [ ] Holdout data has not been examined

Before reporting:
- [ ] All runs included in summary
- [ ] Confidence intervals computed
- [ ] Subgroup analysis completed
- [ ] Limitations documented
- [ ] "Research use only" disclaimer included
