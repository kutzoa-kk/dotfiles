# Prime Directives — sarcopenia-risk-prediction

> Predict sarcopenia risk score from insole gait data using LightGBM with 3-phase validation (score validity, prediction CV, holdout).

## Technical Safeguards

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and `docs/specs/*.md`. Understand the phase structure and gate conditions before writing code.

2. **Immutability**: Never edit files under `data/raw/`. Never implement feature engineering or model training in `notebooks/`. All data access goes through `src/data_access.py`. Use Polars immutable operations — never mutate DataFrames in place.

3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` MUST NEVER appear as a training feature. Run `src/schema/leakage_check.py` before every training run. Violating this invalidates the experiment.

4. **Validation First**: Run `src/schema/data_validation.py` before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds — never on full training set.

5. **Tracking**: Use Hydra + MLflow for experiment management. Run names follow the pattern: `${model.name}_${features.name}_${split.name}_seed${seed}`. NEVER delete experiment runs — all runs including failures must be preserved.

6. **Split Integrity**: `username` is the split unit. All data from the same subject resides in the same fold. See `docs/specs/05_SPLIT_POLICY.md`.

7. **Gate Check**: Phase progression follows strict gates defined in `docs/specs/02_METRICS.md`:
   - **Phase A** -> **Phase B**: Spearman rho >= 0.5
   - **Phase B** -> **Phase C**: Spearman rho >= 0.3
   Hold-out evaluation (Phase C) is ONE-SHOT — do not iterate on hold-out results.

## Scientific Integrity

8. **Anti-Sycophancy**: Do NOT selectively present favorable results. Include ALL experimental runs in summary tables. If results contradict the hypothesis, report them explicitly — never suppress or downplay unfavorable findings. When analysis shows weak or null effects, state this clearly.

9. **Pre-Registration**: Before starting experiments, record hypotheses in `docs/specs/00_HYPOTHESES.md`. Post-hoc findings must be labeled "exploratory" and validated on a separate partition. Never present post-hoc discoveries as pre-registered hypotheses.

10. **Full Reporting**: Final reports must include: (a) total experimental runs attempted, (b) all run results in a summary table, (c) deviations from pre-registered plan with justification, (d) multiple comparison corrections when >1 hypothesis was tested.

## Phase Structure

### Phase A: Score Validation
- **Purpose**: Validate the sarcopenia risk score construct — confirm the target variable is well-defined and correlates with known clinical indicators.
- **Script**: `scripts/run_phase_a.py`
- **Gate**: Spearman rho >= 0.5 between constructed score and expected clinical correlates
- **On failure**: Revise score construction methodology. Do NOT proceed to Phase B.

### Phase B: Prediction Model CV
- **Purpose**: Train LightGBM with GroupKFold 5-fold CV and evaluate whether gait features can predict sarcopenia risk.
- **Script**: `scripts/run_phase_b.py`
- **Gate**: Spearman rho >= 0.3 (OOF predictions vs actual)
- **On failure**: Return to feature engineering or model tuning. Do NOT evaluate on holdout.

### Phase C: Holdout Evaluation
- **Purpose**: One-shot evaluation on held-out 20% of subjects.
- **Script**: `scripts/run_phase_c.py`
- **Gate**: Report metrics (no strict gate — one-shot protocol)
- **On failure**: Document results. Do NOT re-tune and re-evaluate.

## Data Sources

- **InBody data**: `data/raw/` (CSV format)
  - Key columns: username, SMI, body composition metrics
- **Gait features**: `data/raw/` (Parquet format)
  - Key columns: username, walk_features (830 cols), step_features (259 cols)

## Feature Constraints

- Inference-available features: See `src/schema/feature_availability.yaml`
- Feature groups: gender, walk_features (830 cols), step_features (259 cols)
- Feature selection: Domain knowledge
