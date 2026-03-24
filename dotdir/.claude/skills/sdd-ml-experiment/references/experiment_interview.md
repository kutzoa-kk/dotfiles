# Experiment Interview Guide

Conduct the interview using AskUserQuestion. Ask in 2 rounds max.

## Round 1: Experiment Setup

Ask these 4 questions in a single AskUserQuestion call:

### Q1: Experiment Identity
- Experiment name (kebab-case, e.g., `insole-direction-prediction`)
- Location in project tree (e.g., `code/gcrs/kknb/exp002`)
- One-line description of what this experiment tests

### Q2: Prediction Target
- What is the target variable? (e.g., "Direction score (continuous)")
- Task type: "Regression", "Classification", "Multi-task"
- Are there auxiliary targets for multi-task learning?

### Q3: Phase Structure
How many phases does this experiment need?

Default (3-phase):
- **Phase A**: Score/construct validation (is the target variable well-defined?)
- **Phase B**: Prediction model (can we predict the target from features?)
- **Phase C**: Holdout evaluation (does the model generalize?)

Alternatives:
- **2-phase**: Skip Phase A if target is a standard label (e.g., diagnosis)
- **1-phase**: Simple train/test if no phased validation is needed
- **Custom**: User defines phases

### Q4: Data Sources
- What raw data feeds this experiment? (file paths or descriptions)
- What is the subject ID field? (e.g., `username`, `patient_id`)
- Is there existing feature engineering code to reuse?

## Round 2: Experiment Details

Based on Round 1 answers, ask up to 4 targeted questions:

### Feature Engineering (always ask)
- What features are available at inference time?
- What features are NOT available (leak candidates)?
- Do features need aggregation? (e.g., step-level → walk-level)
- Feature selection method: "Domain knowledge (Recommended)", "Nested CV RFE", "LASSO", "Other"

### Model & Training (always ask)
- Model candidates: LightGBM, XGBoost, Linear, etc.
- CV strategy: GroupKFold, StratifiedGroupKFold, TimeSeriesSplit
- Hyperparameter tuning: Optuna nested CV, grid search, or manual

### Gate Conditions (ask if multi-phase)
For each phase, what metric must pass?
Examples:
- Phase A: Spearman ρ(target, expected_correlate) ≥ 0.5
- Phase B: Spearman ρ(predicted, actual) ≥ 0.3 in CV
- Phase C: Same metric on holdout ≥ 0.25

### Holdout Protocol (ask if Phase C exists)
- Holdout type: "Random 80/20", "Temporal", "Facility-based", "Stratified"
- Is holdout one-shot? (Recommended: yes)
- What happens on holdout failure?

## Mapping Answers to Templates

| Answer | Used in |
|--------|---------|
| experiment_name | Directory name, CLAUDE.md header, Hydra config |
| experiment_path | Filesystem location |
| target_variable | HYPOTHESES.md, feature_availability.yaml |
| task_type | METRICS.md metric selection, model config |
| phase_structure | Phase scripts, evaluators, gate conditions |
| data_sources | data_access.py, config.yaml |
| subject_id_field | split config, leakage_check.py |
| features_available | feature_availability.yaml |
| features_unavailable | feature_availability.yaml |
| aggregation_needs | feature_matrix_builder.py, step_aggregator.py |
| model_candidates | model configs, trainer |
| cv_strategy | split config |
| gate_conditions | METRICS.md, phase evaluators |
| holdout_protocol | SPLIT_POLICY.md, Phase C evaluator |
| feature_selection | HYPOTHESES.md analysis plan |
| hp_strategy | model config, trainer |
