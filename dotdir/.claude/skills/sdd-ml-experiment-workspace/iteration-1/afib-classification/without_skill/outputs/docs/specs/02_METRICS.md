# Evaluation Metrics -- AFib Classification

## Phase A: SKIPPED

AF is a standard diagnostic label. No custom score construction phase is required.

## Phase B: ECG Feature-based AF Classification (CV)

### Primary Metric

**PR-AUC** (Precision-Recall Area Under Curve) -- pooled across 5-fold OOF predictions.

Rationale: PR-AUC is robust to class imbalance, which is common in AF datasets.
It focuses on the model's ability to correctly identify AF cases (positive class)
without inflating performance from the majority class.

### Secondary Metrics

- **ROC-AUC** -- Area Under ROC Curve (complementary)
- **F1 Score** -- Harmonic mean of precision and recall (at optimal threshold)
- **Precision** -- At optimal threshold
- **Recall (Sensitivity)** -- At optimal threshold
- **Per-fold PR-AUC** -- Each fold reported individually for stability assessment
- **Calibration** -- Brier score for probability calibration quality

## Phase C: Hold-out ONE-SHOT Evaluation

### Primary Metric

**PR-AUC** on hold-out set.

### Secondary Metrics

- ROC-AUC on hold-out set
- F1, Precision, Recall at optimal threshold (from CV)
- Baseline comparison: PR-AUC of a prevalence-only predictor

## Gate Conditions

| Phase | Condition | Threshold |
|-------|-----------|-----------|
| Phase B -> Phase C | PR-AUC (pooled OOF) | >= 0.70 |
| Phase C -> Deployment | PR-AUC (hold-out) | >= 0.65 |

All gate conditions must be met to progress. Leakage check must also pass.

## Hold-out Evaluation Protocol

- Hold-out evaluation is **ONE-SHOT**: evaluate once, report, do not iterate.
- If hold-out gate fails, do NOT re-tune and re-evaluate.
- Instead: return to CV, diagnose failure, record in deviation log, re-register hypothesis.
- Record hold-out evaluation count (target: 1).

## Multiple Comparison Correction

| Scenario | Method | Formula |
|----------|--------|---------|
| Single hypothesis | None | alpha = 0.05 |
| K independent hypotheses | Bonferroni | alpha_adj = 0.05 / K |
| Model comparison (>= 3 models) | Friedman + Nemenyi | Non-parametric across CV folds |

**Rules:**
- If testing > 1 hypothesis, report BOTH raw and adjusted p-values
- Never report only the best result from multiple runs (disclose total run count)
- Feature selection must be done inside CV folds (nested CV) if data-driven

## Reporting Checklist

Before finalizing results:
- [ ] All experimental runs listed in summary table (not just best)
- [ ] Total run count disclosed
- [ ] Multiple comparison correction applied (if applicable)
- [ ] Exploratory findings labeled
- [ ] Deviations from pre-registered plan documented
- [ ] Negative/null results reported alongside positive results
- [ ] Class distribution reported for train and hold-out sets
- [ ] Per-fold metric stability assessed
