---
name: sdd-experiment-logger
description: >
  Generate per-experiment markdown logs and comparison matrices linked to MLflow run_name
  for SDD ML projects. Creates docs/experiments/{run_name}.md with auto-populated metadata,
  metrics, gate results, and LLM-editable sections (objective, observations, next steps).
  Generates COMPARISON.md with run-over-run parameter diffs and best model tracking.
  Use when: (1) after running experiments, (2) user says "log experiment", "experiment notes",
  "compare experiments", (3) before writing the final report, (4) to track what worked and
  what didn't across experiment iterations.
---

# SDD Experiment Logger

Generate per-experiment markdown logs and comparison matrices, linked to MLflow run_name for traceability.

## Workflow

1. **Collect runs** with sdd-report-generator's `collect_runs.py`
2. **Create experiment log** for each run
3. **Fill observations** (LLM-written sections)
4. **Generate comparison matrix**
5. **Generate final report** (includes Section 6: Experiment Insights)

## Step 1: Ensure Runs Are Collected

```bash
python scripts/collect_runs.py \
    --project-dir <project-root> \
    --backend <mlflow|wandb|local> \
    [backend-specific args] \
    --output data/processed/all_runs.json
```

The `all_runs.json` now includes `run_name` for each run.

## Step 2: Create Experiment Log

Read [references/experiment_log_template.md](references/experiment_log_template.md) for the full template structure.

```bash
python scripts/experiment_logger.py \
    --project-dir <project-root> \
    --run-name <run-name> \
    --runs-json data/processed/all_runs.json
```

This creates `docs/experiments/{run_name}.md` with:
- Auto-populated: run ID, phase, status, timestamps, parameters, metrics, gate results
- LLM-editable: objective, observations (what worked / didn't / unexpected), next steps

## Step 3: Update Observations

After reviewing results, update the LLM-editable sections:

```bash
# Update observations
python scripts/experiment_logger.py \
    --project-dir <project-root> \
    --run-name <run-name> \
    --update-section observations \
    --content "Fold 3 showed overfitting after epoch 15"

# Update next steps
python scripts/experiment_logger.py \
    --project-dir <project-root> \
    --run-name <run-name> \
    --update-section next_steps \
    --content "- [ ] Try learning rate warmup\n- [ ] Add dropout 0.3"
```

Valid sections: `objective`, `observations`, `next_steps`, `related`

## Step 4: Generate Comparison Matrix

Read [references/comparison_template.md](references/comparison_template.md) for the full template structure.

```bash
python scripts/experiment_logger.py \
    --project-dir <project-root> \
    --runs-json data/processed/all_runs.json \
    --generate-comparison
```

This creates `docs/experiments/COMPARISON.md` with:
- Run comparison table (linked to individual logs)
- Automatic parameter change detection between runs
- Best model identification based on gate conditions
- LLM-editable: effective/ineffective techniques, recommended next experiments

## Step 5: Generate Final Report

The final report (sdd-report-generator) now includes Section 6: Experiment Insights, which pulls observations from experiment logs.

## Output Structure

```
docs/experiments/
├── baseline-v1.md      # Per-experiment log
├── feature-eng-v2.md   # Per-experiment log
├── tuned-v3.md         # Per-experiment log
└── COMPARISON.md       # Cross-experiment comparison
```

## Verification Checklist

- [ ] `all_runs.json` contains `run_name` for each run
- [ ] Individual experiment logs exist in `docs/experiments/`
- [ ] Observations sections are filled in (not just placeholders)
- [ ] `COMPARISON.md` generated and reflects all runs
- [ ] Final report Section 6 shows experiment insights
- [ ] Each log links to related experiments (previous/next)

Print the experiment log and comparison matrix and confirm all sections are populated.
