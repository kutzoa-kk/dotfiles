# Hypotheses — sarcopenia-risk-prediction

## Pre-Registered Hypotheses

### H1: Sarcopenia Risk Score Validity (Phase A)
**Hypothesis**: The constructed sarcopenia risk score correlates with established clinical indicators of sarcopenia (e.g., SMI, muscle mass measurements).

- **Metric**: Spearman rho between sarcopenia risk score and clinical correlates
- **Threshold**: rho >= 0.5
- **Rationale**: A valid risk score must demonstrate meaningful association with known clinical measures of sarcopenia.

### H2: Gait Feature Predictability (Phase B)
**Hypothesis**: Insole-derived gait features (walk_features + step_features) can predict sarcopenia risk score with moderate accuracy.

- **Metric**: Spearman rho (OOF predictions vs actual)
- **Threshold**: rho >= 0.3
- **Model**: LightGBM with GroupKFold 5-fold CV
- **Rationale**: Gait patterns are known to deteriorate with muscle loss; insole data should capture these patterns.

### H3: Generalization (Phase C)
**Hypothesis**: The prediction model generalizes to unseen subjects.

- **Metric**: Spearman rho on holdout set (20% of subjects)
- **Protocol**: ONE-SHOT evaluation
- **Rationale**: If the model captures genuine sarcopenia-related gait patterns, it should generalize to new subjects.

## Feature Selection Rationale

Feature selection is based on **domain knowledge**:
- **gender**: Known confound for sarcopenia risk (different cutoffs for male/female)
- **walk_features (830 cols)**: Walk-level gait characteristics from insole sensors
- **step_features (259 cols)**: Step-level biomechanical measurements

## Excluded Features (Leakage Candidates)

The following are excluded because they are either:
- Direct measures of body composition (would trivially predict sarcopenia risk)
- Identity/administrative fields
- Only available during clinical assessment (not at inference)

Excluded: uuid, username, test_date_time, height, weight, age, bmi, smi, vfl

## Analysis Plan

1. **Phase A**: Construct sarcopenia risk score and validate against clinical correlates
2. **Phase B**: Train LightGBM on gait features, evaluate with GroupKFold CV
3. **Phase C**: One-shot holdout evaluation
4. **Post-hoc (exploratory)**: Feature importance analysis, subgroup analysis by gender

Any findings from step 4 must be labeled as **exploratory** and not presented as pre-registered results.
