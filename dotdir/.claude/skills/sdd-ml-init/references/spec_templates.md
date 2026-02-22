# Spec Document Templates (docs/specs/)

Generate each file under `docs/specs/`. Replace `{{placeholders}}` with interview answers.

---

## 00_HYPOTHESES.md

Always generate this file. This is the pre-registration document.

```markdown
# Pre-Registered Hypotheses — {{project_name}}

> This document MUST be written BEFORE any model training or exploratory analysis.
> Changes after experiments begin MUST be tracked via version control with justification.

## Primary Hypothesis

**H1**: {{primary_hypothesis}}
- Expected direction: {{expected_direction}}
- Primary metric: {{primary_metric}}
- Success threshold: {{gate_cv}} (CV), {{gate_holdout}} (hold-out)

## Secondary Hypotheses (if any)

{{For each secondary hypothesis:}}
- **H{{n}}**: {{hypothesis_description}}

## Pre-Registered Analysis Plan

### Feature Set
- Features to be used: As defined in `src/schema/feature_availability.yaml` (inference_available)
- Feature selection method: {{method — e.g., "domain knowledge only" / "recursive feature elimination within CV"}}
- If feature selection is data-driven, it MUST be performed inside CV folds (nested CV)

### Model Candidates
- Models to evaluate: {{model_list — e.g., "LightGBM, Logistic Regression, Random Forest"}}
- Hyperparameter search: {{strategy — e.g., "Optuna within inner CV fold"}}

### Statistical Tests
- Number of hypotheses being tested: {{n_hypotheses}}
- Multiple comparison correction: {{correction_method — e.g., "Bonferroni" / "Benjamini-Hochberg FDR" / "None (single hypothesis)"}}
- Adjusted significance level: {{adjusted_alpha}}

## Exploratory vs Confirmatory Analysis

### Phase 1: Exploratory (EDA)
- Purpose: Data understanding, pattern discovery, hypothesis generation
- Allowed: Unrestricted feature exploration, visualization, correlation analysis
- NOT allowed: Claiming discoveries as confirmed findings
- Output: Updated hypotheses documented as "exploratory findings"

### Phase 2: Confirmatory
- Purpose: Test pre-registered hypotheses only
- Allowed: Running pre-specified models with pre-specified features
- NOT allowed: Changing primary metric, adding features based on Phase 1 results without re-registration
- Output: Accept/reject each hypothesis with confidence intervals

### Phase 3: Post-Hoc (if applicable)
- Purpose: Explore patterns found in Phase 2 results
- Requirement: All findings MUST be labeled as "post-hoc / exploratory"
- Validation: Significant post-hoc findings require independent replication or held-out validation

## Deviation Log

| Date | Original Plan | Deviation | Justification | Approved By |
|------|--------------|-----------|---------------|-------------|
| | | | | |

Any deviation from this plan MUST be recorded here before proceeding.
```

---

## 01_DATA_DICTIONARY.md

```markdown
# Data Dictionary — {{project_name}}

## Variable Catalog

| Variable | Type | Range/Values | Missing Strategy | Notes |
|----------|------|-------------|-----------------|-------|
| {{subject_id_field}} | str | — | Not allowed | Primary key |
| {{for each feature, one row}} | | | | |

## Missing Data Strategy

| Variable Type | Strategy | Rationale |
|--------------|----------|-----------|
| Continuous | MICE or median imputation | Preserves distribution |
| Ordinal (e.g., grade scales) | Ordered imputation or mode | Respects ordinal structure |
| Categorical | Mode or "missing" category | Context-dependent |
| Waveform / sensor | No imputation — use missing flag | Interpolation distorts signal |

## Encoding Rules

- One-hot encoding: Compare against ordinal/target encoding; justify choice with CV comparison.
- Label encoding: Only for ordinal variables with clear ordering.

## Zero-Value Semantics

{{zero_semantics_description}}
```

---

## 02_METRICS.md

```markdown
# Evaluation Metrics — {{project_name}}

## Primary Metric

**{{primary_metric}}** (e.g., PR-AUC for imbalanced classification, RMSE for regression)

Rationale: {{metric_rationale}}

**This metric was fixed at project start and MUST NOT change after seeing results.**
To change the primary metric, document the rationale in `00_HYPOTHESES.md` deviation log
and obtain explicit approval before re-running any experiments.

## Secondary Metrics

{{For classification:}}
- ROC-AUC
- Sensitivity / Specificity / PPV / NPV (at operating threshold)
- F1-score (macro/weighted)

{{For regression:}}
- MAE
- R-squared
- Spearman correlation

## Calibration Metrics

- Brier score
- Calibration slope (target: 0.8-1.2)
- Calibration intercept (target: near 0)

## Multiple Comparison Correction

When testing multiple hypotheses, features, or model configurations:

| Scenario | Correction Method | Formula |
|----------|------------------|---------|
| Single hypothesis | None | alpha = 0.05 |
| K independent hypotheses | Bonferroni | alpha_adj = 0.05 / K |
| K correlated hypotheses | Benjamini-Hochberg FDR | Ranked p-values with FDR control |
| Model comparison (>2 models) | Friedman test + Nemenyi post-hoc | Non-parametric across CV folds |

**Rules:**
- If >1 hypothesis is tested, report BOTH raw and adjusted p-values
- If >3 model variants are compared, use Friedman test across CV folds rather than pairwise t-tests
- Feature selection: If data-driven, must use nested CV; report number of features evaluated
- Never report only the best result from multiple runs without disclosing total run count

## Gate Conditions

| Phase | Condition | Threshold |
|-------|-----------|-----------|
| Internal CV -> Hold-out | {{primary_metric}} >= {{gate_cv}} AND leak check passed AND split integrity verified | Mandatory |
| Hold-out -> Deployment | {{primary_metric}} >= {{gate_holdout}} AND calibration slope 0.8-1.2 | Mandatory |

No model advances to the next phase without meeting ALL gate conditions.

## Hold-Out Evaluation Protocol

- Hold-out evaluation is **ONE-SHOT**: evaluate once, report results, do not iterate.
- If hold-out fails gate conditions, do NOT re-tune and re-evaluate on hold-out.
- Instead: return to CV, diagnose failure, document in deviation log, re-register hypothesis.
- Log the number of times hold-out has been evaluated (target: 1).

## Reporting Checklist

Before finalizing results:
- [ ] All experimental runs listed in summary table (not just the best)
- [ ] Total number of runs disclosed
- [ ] Multiple comparison correction applied (if applicable)
- [ ] Exploratory findings labeled as such
- [ ] Deviations from pre-registered plan documented
- [ ] Null/negative results reported alongside positive results
```

---

## 04_COMPLIANCE.md

Generate only if `compliance_level` is "medical" or "research".

```markdown
# Compliance Requirements — {{project_name}}

## Data Handling

- All PII must be removed or pseudonymized before model training.
- Raw data access is restricted to `src/data_access.py`.

## Regulatory Framework

{{If medical:}}
- GDPR Article 9: Special category data (health) requires explicit consent or research exemption.
- Anonymization: k-anonymity >= 5 for any published results.
- Audit trail: All data transformations logged with timestamps.

{{If research:}}
- IRB/Ethics board approval number: {{to be filled}}
- Data use agreement reference: {{to be filled}}
```

---

## 05_SPLIT_POLICY.md

```markdown
# Data Split Policy — {{project_name}}

## Split Unit

**{{subject_id_field}}** — All data from the same subject MUST reside in the same split.

## Grouping Constraints

{{For each grouping constraint:}}
- **{{constraint_name}}**: {{constraint_description}}

Violating grouping constraints constitutes data leakage and invalidates all results.

## Cross-Validation Strategy

- **Method**: {{cv_strategy}} (e.g., GroupKFold)
- **Folds**: 5 (default)
- **Group key**: {{subject_id_field}}
- **Stratification**: {{stratify_by}}

## Hold-Out Evaluation

- **Method**: {{holdout_strategy}}
{{If facility hold-out:}}
- Leave-One-Facility-Out: Train on N-1 facilities, test on held-out facility.
{{If temporal hold-out:}}
- Train on data before cutoff date, test on data after cutoff.
{{If random hold-out:}}
- 80/20 split respecting subject grouping.

## Split Artifact

Save split assignment as `data/processed/split_index.json` mapping {{subject_id_field}} to fold/split. This serves as an audit artifact.

## Split Verification

Run `src/schema/leakage_check.py --split data/processed/split_index.json` after every split to verify:
- No subject appears in multiple splits
- Intra-subject data (L/R, sessions) is co-located
- Feature matrix contains only inference_available variables
```
