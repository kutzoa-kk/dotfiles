# Compliance -- afib-classification (Research Level)

## Overview

This experiment processes ECG-derived features for atrial fibrillation classification. The following compliance requirements apply at the research level.

## Data Handling

### Data Classification

- **Sensitivity level**: Research data (de-identified ECG features)
- **Identifiers**: `record_id` is a study-assigned identifier, not a direct patient identifier
- **PHI status**: No Protected Health Information (PHI) in the feature dataset; `cardiologist_notes` is excluded from analysis

### Data Storage

- Raw data stored in `data/raw/` (read-only, never modified)
- Processed artifacts stored in `data/processed/`
- No data committed to version control (ensure `.gitignore` coverage)
- Data access restricted to authorized research personnel

### Data Retention

- All experimental runs and results must be preserved for audit
- Split assignments saved as reproducibility artifacts
- Model outputs logged via MLflow for traceability

## Ethics and Regulatory

### Ethics Review

- Research protocol must be reviewed by appropriate ethics board (IRB or equivalent) before data collection
- Informed consent requirements must be documented
- Data use agreement (DUA) must cover secondary analysis purposes

### Regulatory Considerations

- This is a research-stage experiment; clinical deployment requires separate regulatory approval
- AF classification models intended for clinical use must comply with applicable medical device regulations (e.g., FDA 510(k), CE marking)
- Results must not be used for clinical decision-making without proper validation and regulatory clearance

## Reproducibility

### Requirements

1. **Fixed random seeds**: All random operations use `seed=42` or configurable seed
2. **Environment specification**: Dependencies locked via `uv.lock` or `requirements.txt`
3. **Version control**: All code changes tracked in git
4. **Experiment tracking**: All runs logged via MLflow with:
   - Hyperparameters
   - Metrics (per-fold and aggregate)
   - Model artifacts
   - Split assignments

### Audit Trail

- Every experiment run is logged (including failures)
- No experiment runs are deleted
- Deviations from pre-registered plan documented in `docs/specs/00_HYPOTHESES.md`
- Holdout evaluation count tracked to enforce one-shot protocol

## Reporting Standards

### Required in Publications

1. Full dataset description (size, class distribution, feature set)
2. Complete CV results (per-fold, not just aggregate)
3. All models attempted (not just the best-performing)
4. Feature importance analysis
5. Limitations and potential biases
6. Comparison with relevant baselines

### Anti-P-Hacking Measures

1. Hypotheses pre-registered before experimentation
2. Phase gates prevent iterating on holdout results
3. All experimental runs preserved and reported
4. Post-hoc findings explicitly labeled as exploratory
5. Multiple comparison corrections applied when testing >1 hypothesis

## Checklist Before Submission

- [ ] Ethics review approved
- [ ] Data use agreement in place
- [ ] All experimental runs documented
- [ ] Pre-registered hypotheses match reported analyses
- [ ] Holdout evaluated exactly once
- [ ] Feature leakage check passed
- [ ] Reproducibility verified (re-run from clean state)
- [ ] Limitations section included in manuscript
