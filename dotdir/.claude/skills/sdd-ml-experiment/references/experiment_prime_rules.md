# Experiment Prime Rules Template (CLAUDE.md)

Generate experiment-level CLAUDE.md by replacing `{{placeholders}}` with interview answers.

```markdown
# Prime Directives — {{experiment_name}}

> {{experiment_description}}

## Technical Safeguards

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and `docs/specs/*.md`. Understand the phase structure and gate conditions before writing code.

2. **Immutability**: Never edit files under `data/raw/`. Never implement feature engineering or model training in `notebooks/`. All data access goes through `src/data_access.py`. Use Polars immutable operations — never mutate DataFrames in place.

3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` MUST NEVER appear as a training feature. Run `src/schema/leakage_check.py` before every training run. Violating this invalidates the experiment.

4. **Validation First**: Run `src/schema/data_validation.py` before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds — never on full training set.

5. **Tracking**: Use {{experiment_tool}} for experiment management. Run names follow the pattern: `${model.name}_${features.name}_${split.name}_seed${seed}`. NEVER delete experiment runs — all runs including failures must be preserved.

6. **Split Integrity**: `{{subject_id_field}}` is the split unit. All data from the same subject resides in the same fold. {{grouping_constraints_summary}}. See `docs/specs/05_SPLIT_POLICY.md`.

7. **Gate Check**: Phase progression follows strict gates defined in `docs/specs/02_METRICS.md`:
{{For each phase:}}
   - **Phase {{phase_letter}}** → **Phase {{next_phase_letter}}**: {{gate_metric}} {{gate_operator}} {{gate_threshold}}
   Hold-out evaluation (Phase C) is ONE-SHOT — do not iterate on hold-out results.

## Scientific Integrity

8. **Anti-Sycophancy**: Do NOT selectively present favorable results. Include ALL experimental runs in summary tables. If results contradict the hypothesis, report them explicitly — never suppress or downplay unfavorable findings. When analysis shows weak or null effects, state this clearly.

9. **Pre-Registration**: Before starting experiments, record hypotheses in `docs/specs/00_HYPOTHESES.md`. Post-hoc findings must be labeled "exploratory" and validated on a separate partition. Never present post-hoc discoveries as pre-registered hypotheses.

10. **Full Reporting**: Final reports must include: (a) total experimental runs attempted, (b) all run results in a summary table, (c) deviations from pre-registered plan with justification, (d) multiple comparison corrections when >1 hypothesis was tested.

## Phase Structure

{{For each phase:}}
### Phase {{phase_letter}}: {{phase_name}}
- **Purpose**: {{phase_purpose}}
- **Script**: `scripts/run_phase_{{phase_letter_lower}}.py`
- **Gate**: {{gate_condition}}
- **On failure**: {{failure_action}}

## Data Sources

{{For each data source:}}
- **{{source_name}}**: `{{source_path}}`
  - Format: {{format}}
  - Key columns: {{key_columns}}

## Feature Constraints

- Inference-available features: See `src/schema/feature_availability.yaml`
- Standardization: {{standardization_strategy — e.g., "z-score within sex × measurement_month"}}
- Feature selection: {{feature_selection_method}}
```

## Customization Rules

- If `compliance_level == "medical"`: Add rule 11 referencing `docs/specs/04_COMPLIANCE.md`
- If `experiment_tool == "Hydra + MLflow"`: Rule 5 references Hydra config under `conf/`
- If `experiment_tool == "W&B"`: Rule 5 references `wandb.init()` config
- If no grouping constraints: Remove grouping sentence from rule 6
- If 2-phase (no Phase A): Adjust phase structure section
- If 1-phase: Simplify gate check to single pass/fail
