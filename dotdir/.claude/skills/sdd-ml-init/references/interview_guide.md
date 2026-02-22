# Interview Guide

Conduct the interview using AskUserQuestion. Ask in 2 rounds max to minimize friction.

## Round 1: Core Project Setup

Ask these 4 questions in a single AskUserQuestion call:

### Q1: Project Overview
- Project name (kebab-case for directory, e.g. `knee-oa-prediction`)
- One-line description of prediction target
- Options: "Classification", "Regression", "Multi-task", "Unsupervised/Clustering"

### Q2: Data Characteristics
- Data modality (tabular / time-series / image / multimodal)
- Subject-level grouping field name (e.g. `subject_id`, `patient_id`)
- Additional grouping constraints (e.g. L/R limb, session, facility)

### Q3: Experiment Management
- Tool preference: "Hydra + MLflow (Recommended)", "Weights & Biases", "Neptune", "Custom / None"

### Q4: Compliance Level
- "Medical device / clinical trial (strict)", "Research (standard)", "Internal / exploratory (minimal)"

## Round 2: Domain-Specific Details

Based on Round 1 answers, ask up to 4 targeted questions:

### Features (always ask)
- List inference-available features (comma-separated)
- List inference-unavailable features (leak candidates)
- Auxiliary targets for multi-task learning (optional)

### Split Policy (ask if grouping fields identified)
- Preferred CV strategy: "GroupKFold (Recommended)", "StratifiedGroupKFold", "LeaveOneGroupOut", "TimeSeriesSplit"
- Hold-out strategy: "Facility hold-out", "Temporal hold-out", "Random hold-out", "None"

### Metrics & Gate Conditions (ask if classification or regression identified)
- For classification: primary metric default = PR-AUC
- For regression: primary metric default = RMSE
- Gate threshold for CV (e.g. PR-AUC >= 0.70)
- Gate threshold for hold-out (e.g. PR-AUC >= 0.65)

### Hypothesis & Pre-Registration (always ask)
- Primary hypothesis: What do you expect to find? (e.g. "Feature set X predicts outcome Y with PR-AUC > 0.70")
- Expected direction of effect (e.g. "higher feature values → higher risk")
- Number of hypotheses to test (for multiple comparison correction):
  - "1 (no correction needed)"
  - "2-5 (Bonferroni correction)"
  - ">5 (Benjamini-Hochberg FDR)"
- Model candidates to evaluate (e.g. "LightGBM, Logistic Regression, Random Forest")
- Feature selection method: "Domain knowledge only (Recommended)", "Recursive feature elimination (nested CV)", "LASSO (nested CV)", "Other"

**Note on Validation question**: Ask only if time-series or sensor data was selected in Round 1.
- Sampling rate (Hz)
- Zero-value semantics: "non-contact / valid zero", "missing / sensor off", "both possible"
- Accepted value range per channel (optional)

If Round 2 reaches the 4-question limit, merge Hypothesis into Metrics as a combined question.

## Mapping Answers to Templates

After interview, map answers to template placeholders:

| Answer | Used in |
|--------|---------|
| project_name | Directory name, CLAUDE.md header |
| task_type | METRICS.md primary metric selection |
| features_available | feature_availability.yaml |
| features_unavailable | feature_availability.yaml |
| subject_id_field | SPLIT_POLICY.md, data_validation.py |
| grouping_constraints | SPLIT_POLICY.md |
| cv_strategy | SPLIT_POLICY.md |
| holdout_strategy | SPLIT_POLICY.md |
| primary_metric | METRICS.md |
| gate_cv | METRICS.md |
| gate_holdout | METRICS.md |
| experiment_tool | CLAUDE.md rule 5, conf/ templates |
| compliance_level | COMPLIANCE.md detail level |
| sampling_rate | data_validation.py |
| zero_semantics | DATA_DICTIONARY.md |
| primary_hypothesis | 00_HYPOTHESES.md |
| expected_direction | 00_HYPOTHESES.md |
| n_hypotheses | 00_HYPOTHESES.md, 02_METRICS.md correction method |
| correction_method | 00_HYPOTHESES.md, 02_METRICS.md |
| model_list | 00_HYPOTHESES.md analysis plan |
| feature_selection_method | 00_HYPOTHESES.md analysis plan |
