---
name: sdd-experiment-audit
description: >
  Audit experiment tracking integrity for SDD ML projects. Runs 5 checks enforcing
  R5 (Tracking), R7 (Gate Conditions), and R9 (Pre-Registration): (1) deleted run detection,
  (2) hold-out count limit, (3) CV gate before hold-out, (4) pre-registration timing,
  (5) spec drift detection. Supports MLflow, W&B, and local backends.
  Includes a separate deviation checker that cross-references 00_HYPOTHESES.md with git history.
  Use when: (1) after running experiments, (2) user says "audit experiments", "check experiment
  integrity", "deviation check", (3) before reporting results, (4) CI gate for experiment quality.
---

# SDD Experiment Audit

Audit experiment tracking to detect deleted runs, gate violations, pre-registration timing issues, and undocumented specification changes.

## Workflow

1. **Configure** experiment backend connection
2. **Run** experiment audit (`scripts/experiment_audit.py`)
3. **Run** deviation checker (`scripts/deviation_checker.py`)
4. **Fix** any failures
5. **Verify** all checks pass

## Step 1: Configure Backend

Determine the experiment tracking backend:

| Backend | Required Arguments |
|---------|-------------------|
| MLflow | `--backend mlflow --tracking-uri <URI> --experiment-name <NAME>` |
| W&B | `--backend wandb --entity <TEAM> --wandb-project <PROJECT>` |
| Local | `--backend local --runs-dir <PATH>` (default: `data/processed/runs/`) |

Read [references/backend_configs.md](references/backend_configs.md) for API patterns and RunInfo abstraction.

## Step 2: Run Experiment Audit

Read [references/audit_checks.md](references/audit_checks.md) for detailed check definitions.

```bash
python scripts/experiment_audit.py \
    --project-dir <project-root> \
    --backend <mlflow|wandb|local> \
    [backend-specific args]
```

The script runs 5 checks:

| # | Check | Rule | What it detects |
|---|-------|------|-----------------|
| 1 | Deleted Runs | R5 | Runs removed from tracking system |
| 2 | Hold-out Count | R7 | Multiple hold-out evaluations (must be ≤1) |
| 3 | Gate Conditions | R7 | Hold-out without prior CV gate pass |
| 4 | Pre-Registration | R9 | Experiments before hypothesis commit |
| 5 | Spec Drift | R9 | Post-experiment spec changes without deviation log |

## Step 3: Run Deviation Checker

The deviation checker provides detailed analysis of spec changes vs deviation log entries:

```bash
python scripts/deviation_checker.py \
    --project-dir <project-root>
```

This checks:
- **Coverage**: Every spec file modification in git has a matching deviation log entry
- **Completeness**: Every deviation entry has required fields (date, file, description)

## Step 4: Handle Failures

### Deleted Runs
- **NEVER** re-delete runs. Investigate why they were deleted.
- If using MLflow: restore via `mlflow.tracking.MlflowClient().restore_run(run_id)`
- If permanently lost: document in deviation log with full context

### Hold-out Count > 1
- Re-tag extra hold-out runs as `phase=exploratory_holdout`
- Document in 00_HYPOTHESES.md Deviation Log
- Only the FIRST hold-out run counts as confirmatory

### Gate Not Met
- If hold-out was premature: tag as exploratory, re-run CV first
- If gate threshold needs revision: update 02_METRICS.md, log deviation

### Pre-Registration Timing
- If hypotheses exist but uncommitted: commit immediately, label existing results exploratory
- If hypotheses written after experiments: ALL results are exploratory

### Spec Drift
- Add entries to the Deviation Log table in 00_HYPOTHESES.md:

```markdown
| Date | File Changed | Description | Rationale | Impact |
|------|-------------|-------------|-----------|--------|
| 2024-01-20 | 02_METRICS.md | Added F1 as secondary metric | Reviewer request | Exploratory |
```

## Step 5: Verify

After fixes, re-run both scripts:

```bash
python scripts/experiment_audit.py --project-dir . --backend local
python scripts/deviation_checker.py --project-dir .
```

## Verification Checklist

- [ ] All 5 experiment audit checks return `[PASS]`
- [ ] Both deviation checker checks return `[PASS]`
- [ ] No deleted runs in experiment tracking system
- [ ] At most 1 hold-out run exists
- [ ] CV gate conditions met before any hold-out evaluation
- [ ] 00_HYPOTHESES.md committed before first experiment run
- [ ] All post-experiment spec changes documented in Deviation Log
- [ ] Deviation Log entries have all required fields

Print both reports and confirm all checks pass.
