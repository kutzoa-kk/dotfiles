# Prime Directives -- afib-classification

> ECG feature-based atrial fibrillation (AF) classification using RR intervals, P-wave morphology, QRS complex features, and heart rate variability metrics. 2-phase experiment: Phase B (CV classification) and Phase C (holdout evaluation).

## Technical Safeguards

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and `docs/specs/*.md`. Understand the phase structure and gate conditions before writing code.

2. **Immutability**: Never edit files under `data/raw/`. Never implement feature engineering or model training in `notebooks/`. All data access goes through `src/data_access.py`. Use Polars immutable operations -- never mutate DataFrames in place.

3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` MUST NEVER appear as a training feature. Run `src/schema/leakage_check.py` before every training run. Violating this invalidates the experiment.

4. **Validation First**: Run `src/schema/data_validation.py` before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds -- never on full training set.

5. **Tracking**: Use Hydra + MLflow for experiment management. Run names follow the pattern: `${model.name}_${features.name}_${split.name}_seed${seed}`. NEVER delete experiment runs -- all runs including failures must be preserved.

6. **Split Integrity**: `record_id` is the split unit. All data from the same record resides in the same fold. Use StratifiedGroupKFold to ensure class balance across folds while respecting record grouping. See `docs/specs/05_SPLIT_POLICY.md`.

7. **Gate Check**: Phase progression follows strict gates defined in `docs/specs/02_METRICS.md`:
   - **Phase B** -> **Phase C**: PR-AUC >= 0.70 (mean across CV folds)
   - Hold-out evaluation (Phase C) is ONE-SHOT -- do not iterate on hold-out results.
   - Phase C gate: PR-AUC >= 0.65 on holdout set.

## Scientific Integrity

8. **Anti-Sycophancy**: Do NOT selectively present favorable results. Include ALL experimental runs in summary tables. If results contradict the hypothesis, report them explicitly -- never suppress or downplay unfavorable findings. When analysis shows weak or null effects, state this clearly.

9. **Pre-Registration**: Before starting experiments, record hypotheses in `docs/specs/00_HYPOTHESES.md`. Post-hoc findings must be labeled "exploratory" and validated on a separate partition. Never present post-hoc discoveries as pre-registered hypotheses.

10. **Full Reporting**: Final reports must include: (a) total experimental runs attempted, (b) all run results in a summary table, (c) deviations from pre-registered plan with justification, (d) multiple comparison corrections when >1 hypothesis was tested.

11. **Compliance**: This experiment follows research-level compliance requirements. See `docs/specs/04_COMPLIANCE.md` for data handling, ethics review, and reporting standards.

## Phase Structure

### Phase B: Classification Model CV
- **Purpose**: Train LightGBM and Logistic Regression classifiers with StratifiedGroupKFold 5-fold CV; evaluate AF classification performance
- **Script**: `scripts/run_phase_b.py`
- **Gate**: PR-AUC >= 0.70 (mean across folds)
- **On failure**: Return to feature engineering and model diagnostics. Do NOT proceed to Phase C.

### Phase C: Holdout Evaluation
- **Purpose**: One-shot evaluation of the best Phase B model on held-out 20% test set
- **Script**: `scripts/run_phase_c.py`
- **Gate**: PR-AUC >= 0.65
- **On failure**: Do NOT re-tune. Return to CV and document deviation from expected performance.

## Data Sources

- **ECG Features**: `data/raw/ecg_features.parquet`
  - Format: Parquet
  - Key columns: record_id, RR interval features, P-wave features, QRS features, HRV features
- **Clinical Labels**: `data/raw/clinical_labels.csv`
  - Format: CSV
  - Key columns: record_id, af_label (binary: 0=no AF, 1=AF)

## Feature Constraints

- Inference-available features: See `src/schema/feature_availability.yaml`
- Standardization: z-score normalization fit within each CV fold
- Feature selection: Domain knowledge (ECG morphology and rhythm features known to be relevant to AF)
