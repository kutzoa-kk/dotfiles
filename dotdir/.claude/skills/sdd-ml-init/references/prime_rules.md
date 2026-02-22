# Prime Rules Template (CLAUDE.md)

Generate CLAUDE.md by replacing `{{placeholders}}` with interview answers.

```markdown
# Prime Directives for ML Agent — {{project_name}}

> {{project_description}}

1. **Routing**: Before any implementation, read `src/schema/feature_availability.yaml` and relevant `docs/specs/*.md`.
2. **Immutability**: Never edit files under `data/raw/`. Never implement feature engineering or model training in `notebooks/`. All data access goes through `src/data_access.py`.
3. **No Leakage**: Any variable marked `inference_unavailable` in `feature_availability.yaml` must NEVER appear as a training feature. Violating this fails the task immediately. Run `src/schema/leakage_check.py` before every training run.
4. **Validation First**: Run `src/schema/data_validation.py` (Pandera) before any data processing. All preprocessing (Scaler, Imputer, etc.) must be fit INSIDE CV folds — never on full training set.
5. **Tracking**: Use {{experiment_tool}} for experiment management. Run names must be dynamically generated from config values. NEVER delete experiment runs. All runs — including failed and unfavorable ones — must be preserved.
6. **Split Integrity**: Data splitting follows `docs/specs/05_SPLIT_POLICY.md`. {{subject_id_field}} is the split unit. {{grouping_constraints_summary}}.
7. **Gate Check**: No model progresses to hold-out evaluation unless internal CV meets the gate conditions in `docs/specs/02_METRICS.md`. Hold-out evaluation is ONE-SHOT — do not iterate on hold-out results.
8. **Anti-Sycophancy**: Do NOT selectively present favorable results. When reporting, include ALL experimental runs in a summary table. If results contradict the user's hypothesis, report them explicitly — never suppress or downplay unfavorable findings. When analysis shows weak or null effects, state this clearly rather than searching for alternative framings that appear more positive.
9. **Pre-Registration**: Before starting experiments, record hypotheses and analysis plan in `docs/specs/00_HYPOTHESES.md`. Any post-hoc findings must be clearly labeled as "exploratory" and validated on a separate data partition. Never present post-hoc discoveries as if they were pre-registered hypotheses.
10. **Full Reporting**: Final reports must include: (a) total number of experimental runs attempted, (b) all run results in a summary table, (c) any deviations from the pre-registered plan with justification, (d) multiple comparison corrections applied when >1 hypothesis was tested.
```

## Customization Rules

- If `compliance_level == "medical"`: Add rule 11 about GDPR/anonymization referencing `docs/specs/04_COMPLIANCE.md`
- If `experiment_tool == "Hydra + MLflow"`: Rule 5 references Hydra config under `conf/`
- If `experiment_tool == "Weights & Biases"`: Rule 5 references `wandb.init()` config
- If no grouping constraints: Remove the grouping sentence from rule 6
