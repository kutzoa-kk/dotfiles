# Comparison Matrix Template

This template defines the structure for `docs/experiments/COMPARISON.md`.

## Structure

```markdown
# Experiment Comparison Matrix

**Generated**: {timestamp}
**Total Runs**: {count}

## Run Comparison

| Run Name | Phase | Status | Primary Metric | Key Change | Outcome |
|----------|-------|--------|---------------|------------|---------|
| [run-name](./run-name.md) | cv | FINISHED | 0.8234 | Initial run | PASS |
| [run-v2](./run-v2.md) | cv | FINISHED | 0.8456 | lr: 0.01->0.001 | PASS |

## Effective Techniques
{List techniques that consistently improved metrics}

## Ineffective Techniques
{List techniques that did not improve or hurt metrics}

## Current Best Model
**Run**: [best-run](./best-run.md)
**{primary_metric}**: {best_value}

## Recommended Next Experiments
{Based on the patterns observed, suggest next experiments}
```

## Column Descriptions

| Column | Description | Source |
|--------|-------------|--------|
| Run Name | Linked to individual experiment log | `run_name` field |
| Phase | cv / holdout / exploratory | `phase` field |
| Status | FINISHED / FAILED / RUNNING | `status` field |
| Primary Metric | Value of the first gate metric from `02_METRICS.md` | `metrics` + gate conditions |
| Key Change | Detected parameter differences vs previous run | `params` diff |
| Outcome | PASS/FAIL based on gate conditions | gate evaluation |

## Key Change Detection

The comparison matrix automatically detects parameter changes between consecutive runs:

- `+param=value` -- new parameter added
- `-param` -- parameter removed
- `param: old->new` -- parameter value changed
- Shows up to 3 changes per run

## Generation

```bash
python experiment_logger.py --project-dir . \
    --runs-json data/processed/all_runs.json \
    --generate-comparison
```

## LLM-Populated Sections

After generation, the LLM should fill in:

1. **Effective Techniques** -- patterns that consistently improved the primary metric
2. **Ineffective Techniques** -- approaches that did not help or hurt performance
3. **Recommended Next Experiments** -- data-driven suggestions for what to try next
