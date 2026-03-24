# Prime Directives for ML Agent -- AFib Classification

> ECG feature-based atrial fibrillation (AF) binary classification.
> Phase A is skipped (AF is a standard diagnostic label).
> Phase B: 5-fold StratifiedGroupKFold CV (PR-AUC >= 0.70).
> Phase C: Hold-out ONE-SHOT evaluation (PR-AUC >= 0.65).

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and relevant `docs/specs/*.md`.
2. **Immutability**: Never edit files under `data/raw/`. All data access goes through `src/data_access.py`.
3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` must NEVER appear as a training feature. Violating this fails the task immediately. Run `src/schema/leakage_check.py` before every training run.
4. **Validation First**: Run `src/schema/data_validation.py` before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds -- never on full training set.
5. **Split Integrity**: Data splitting follows `docs/specs/05_SPLIT_POLICY.md`. `record_id` is the split unit. All records from the same subject must reside in the same fold.
6. **Gate Check**: No model progresses to hold-out evaluation unless internal CV meets the gate conditions in `docs/specs/02_METRICS.md`. Hold-out evaluation is ONE-SHOT -- do not iterate on hold-out results.
7. **Anti-Sycophancy**: Do NOT selectively present favorable results. When reporting, include ALL experimental runs in a summary table. If results contradict the user's hypothesis, report them explicitly -- never suppress or downplay unfavorable findings.
8. **Pre-Registration**: Before starting experiments, record hypotheses and analysis plan in `docs/specs/00_HYPOTHESES.md`. Any post-hoc findings must be clearly labeled as "exploratory".
9. **Full Reporting**: Final reports must include: (a) total number of experimental runs attempted, (b) all run results in a summary table, (c) any deviations from the pre-registered plan with justification, (d) multiple comparison corrections applied when >1 hypothesis was tested.

## Data Constraints (Critical)

- Target: `af_label` (binary: 0 = no AF, 1 = AF)
- Subject ID: `record_id` (grouping key for splits)
- ECG features: RR intervals, P-wave morphology, QRS features, heart rate variability
- Features PROHIBITED from training: `record_id`, `diagnosis_date`, `af_label`, `cardiologist_notes`
- Models: LightGBM, Logistic Regression
- CV: StratifiedGroupKFold (5-fold, grouped by `record_id`)
- Phase A: SKIPPED (AF is a standard diagnostic label, no custom score construction needed)
