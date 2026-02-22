# Experiment Log Template

This template defines the structure for per-experiment markdown logs in `docs/experiments/{run_name}.md`.

## Structure

```markdown
# Experiment: {run_name}

| Field | Value |
|-------|-------|
| Run ID | `{run_id}` |
| Run Name | {run_name} |
| Phase | {phase} |
| Status | {status} |
| Started | {start_time} |
| Completed | {end_time} |

## Objective

{LLM describes the hypothesis or goal for this experiment}

## Configuration

| Parameter | Value |
|-----------|-------|
| {param_name} | {param_value} |

## Results

| Metric | Value | Gate | Status |
|--------|-------|------|--------|
| {metric_name} | {value} | {gate_condition} | PASS/FAIL |

## Observations

### What Worked
{Describe what produced positive results}

### What Didn't Work
{Describe what did not meet expectations}

### Unexpected Findings
{Note any surprising observations}

## Next Steps
- [ ] {Suggested follow-up experiment or action}

## Related Experiments
- Previous: [{prev_run_name}](./{prev_run_name}.md)
- Next: [{next_run_name}](./{next_run_name}.md)
```

## Field Descriptions

| Field | Source | Auto-populated |
|-------|--------|---------------|
| Run ID | `all_runs.json` -> `run_id` | Yes |
| Run Name | `all_runs.json` -> `run_name` | Yes |
| Phase | `all_runs.json` -> `phase` | Yes |
| Status | `all_runs.json` -> `status` | Yes |
| Started / Completed | `all_runs.json` -> `start_time` / `end_time` | Yes |
| Configuration | `all_runs.json` -> `params` | Yes |
| Results | `all_runs.json` -> `metrics` + `02_METRICS.md` gates | Yes |
| Objective | LLM-written | No |
| Observations | LLM-written | No |
| Next Steps | LLM-written | No |
| Related Experiments | Auto-linked by timestamp order | Partial |

## Update Commands

Update specific sections after creation:

```bash
# Update observations
python experiment_logger.py --project-dir . --run-name baseline-v1 \
    --update-section observations --content "Fold 3 overfitting after epoch 15"

# Update next steps
python experiment_logger.py --project-dir . --run-name baseline-v1 \
    --update-section next_steps --content "- [ ] Try learning rate warmup\n- [ ] Add dropout 0.3"
```

## Valid Sections for Update

| Section Key | Maps To |
|-------------|---------|
| `objective` | `## Objective` |
| `observations` | `## Observations` |
| `next_steps` | `## Next Steps` |
| `related` | `## Related Experiments` |
