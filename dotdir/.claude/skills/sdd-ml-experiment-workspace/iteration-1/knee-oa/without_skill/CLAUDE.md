# Prime Directives for ML Agent — Knee OA Progression

> Predict KL grade (0-4) from knee joint angle time-series data for osteoarthritis progression assessment. Ordinal regression with medical-level compliance.

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and relevant `docs/specs/*.md`.
2. **Immutability**: Never edit files under `data/raw/`. Never implement feature engineering or model training in `notebooks/`. All data access goes through `src/data_access.py`.
3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` must NEVER appear as a training feature. Violating this fails the task immediately. Run `src/schema/leakage_check.py` before every training run.
4. **Validation First**: Run `src/schema/data_validation.py` (Pandera) before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds -- never on full training set.
5. **Tracking**: Use Hydra + MLflow for experiment management. Hydra config lives under `conf/`. Run names must be dynamically generated from config values. NEVER delete experiment runs. All runs -- including failed and unfavorable ones -- must be preserved.
6. **Split Integrity**: Data splitting follows `docs/specs/05_SPLIT_POLICY.md`. `patient_id` is the split unit. All measurements from the same subject (L/R sides, multiple visits) must reside in the same fold.
7. **Gate Check**: No model progresses to hold-out evaluation unless internal CV meets the gate conditions in `docs/specs/02_METRICS.md`. Hold-out evaluation is ONE-SHOT -- do not iterate on hold-out results.
8. **Anti-Sycophancy**: Do NOT selectively present favorable results. When reporting, include ALL experimental runs in a summary table. If results contradict the user's hypothesis, report them explicitly -- never suppress or downplay unfavorable findings.
9. **Pre-Registration**: Before starting experiments, record hypotheses and analysis plan in `docs/specs/00_HYPOTHESES.md`. Any post-hoc findings must be clearly labeled as "exploratory" and validated on a separate data partition. Never present post-hoc discoveries as if they were pre-registered hypotheses.
10. **Full Reporting**: Final reports must include: (a) total number of experimental runs attempted, (b) all run results in a summary table, (c) any deviations from the pre-registered plan with justification, (d) multiple comparison corrections applied when >1 hypothesis was tested.
11. **Medical Compliance**: This is a medical-grade prediction system. All results must include confidence intervals, calibration plots, and clinical interpretability analysis. Model predictions must be validated against domain knowledge.

## Data Constraints (Critical)

- Target: KL grade (0-4, ordinal)
- Data sources: Joint angle time-series (HDF5, 100 Hz), clinical metadata (CSV)
- Subject ID: patient_id
- Grouping: side (L/R) co-located with patient_id
- Holdout: Temporal split (train < 2024, test >= 2024)
- Sampling rate: 100 Hz

## Feature Constraints

- **Available**: knee_angle_features, gait_cycle_features, demographic (age, sex)
- **Unavailable (FORBIDDEN)**: patient_id, visit_date, kl_grade, radiograph_score
