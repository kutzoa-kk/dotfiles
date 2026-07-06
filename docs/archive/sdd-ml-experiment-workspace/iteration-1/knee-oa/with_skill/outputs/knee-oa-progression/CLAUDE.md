# Prime Directives — knee-oa-progression

> Predict KL grade (0-4, ordinal regression) of knee osteoarthritis progression from knee joint angle time-series data at 100 Hz, with patient_id grouping and left/right knee co-location.

## Technical Safeguards

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and `docs/specs/*.md`. Understand the phase structure and gate conditions before writing code.

2. **Immutability**: Never edit files under `data/raw/`. Never implement feature engineering or model training in `notebooks/`. All data access goes through `src/data_access.py`. Use Polars immutable operations — never mutate DataFrames in place.

3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` MUST NEVER appear as a training feature. Run `src/schema/leakage_check.py` before every training run. Violating this invalidates the experiment.

4. **Validation First**: Run `src/schema/data_validation.py` before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds — never on full training set.

5. **Tracking**: Use Hydra + MLflow for experiment management. Run names follow the pattern: `${model.name}_${features.name}_${split.name}_seed${seed}`. NEVER delete experiment runs — all runs including failures must be preserved.

6. **Split Integrity**: `patient_id` is the split unit. All data from the same patient resides in the same fold. Left/right knee (`side`) data for the same patient must be co-located in the same fold — never split across folds. See `docs/specs/05_SPLIT_POLICY.md`.

7. **Gate Check**: Phase progression follows strict gates defined in `docs/specs/02_METRICS.md`:
   - **Phase A** -> **Phase B**: Spearman rho >= 0.4 (biomarker correlation)
   - **Phase B** -> **Phase C**: RMSE <= 1.0 (regression CV)
   Hold-out evaluation (Phase C) is ONE-SHOT — do not iterate on hold-out results.

## Scientific Integrity

8. **Anti-Sycophancy**: Do NOT selectively present favorable results. Include ALL experimental runs in summary tables. If results contradict the hypothesis, report them explicitly — never suppress or downplay unfavorable findings. When analysis shows weak or null effects, state this clearly.

9. **Pre-Registration**: Before starting experiments, record hypotheses in `docs/specs/00_HYPOTHESES.md`. Post-hoc findings must be labeled "exploratory" and validated on a separate partition. Never present post-hoc discoveries as pre-registered hypotheses.

10. **Full Reporting**: Final reports must include: (a) total experimental runs attempted, (b) all run results in a summary table, (c) deviations from pre-registered plan with justification, (d) multiple comparison corrections when >1 hypothesis was tested.

11. **Medical Compliance**: This experiment operates under medical compliance level. All requirements in `docs/specs/04_COMPLIANCE.md` must be followed. Model outputs must include confidence intervals and uncertainty estimates. Decisions based on model predictions must be reviewed by qualified medical professionals. See `docs/specs/04_COMPLIANCE.md` for full requirements.

## Phase Structure

### Phase A: Biomarker Correlation Validation
- **Purpose**: Validate that KL grade correlates with known biomechanical biomarkers (knee angle features, gait cycle parameters) before building prediction models.
- **Script**: `scripts/run_phase_a.py`
- **Gate**: Spearman rho >= 0.4 between KL grade and at least one biomarker group
- **On failure**: Re-examine biomarker definitions and data quality. Do NOT proceed to Phase B.

### Phase B: Regression Model CV
- **Purpose**: Train ordinal regression models (LightGBM, XGBoost) with GroupKFold CV to predict KL grade from knee angle features.
- **Script**: `scripts/run_phase_b.py`
- **Gate**: RMSE <= 1.0 on cross-validated OOF predictions
- **On failure**: Diagnose feature engineering, model selection, or data quality issues. Do NOT proceed to Phase C.

### Phase C: Holdout Evaluation
- **Purpose**: One-shot evaluation on temporal holdout (train < 2024, test >= 2024).
- **Script**: `scripts/run_phase_c.py`
- **Gate**: Report RMSE, MAE, and ordinal accuracy on holdout. No re-tuning allowed.
- **On failure**: Document deviation. Do NOT re-tune and re-evaluate.

## Data Sources

- **Joint angle time-series**: `data/raw/joint_angles.h5`
  - Format: HDF5 (100 Hz sampling rate)
  - Key columns: patient_id, side (L/R), knee_angle (time-series), visit_date
  - Zero semantics: non-contact / valid zero

- **Clinical metadata**: `data/raw/clinical_metadata.csv`
  - Format: CSV
  - Key columns: patient_id, side, kl_grade, age, sex, bmi, visit_date

## Feature Constraints

- Inference-available features: See `src/schema/feature_availability.yaml`
- Standardization: z-score within sex x age_group for demographic features; raw for time-series derived features
- Feature selection: Nested CV RFE (Recursive Feature Elimination within inner CV loop)
