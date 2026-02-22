# Experiment Audit: Check Definitions

Five automated checks that enforce SDD prime rules R5 (Tracking), R7 (Gate), and R9 (Pre-Registration) during and after experimentation.

---

## Check 1: Deleted Runs Detection (R5)

**Rule enforced**: Never delete experiment runs. All runs (including failed) must be preserved.

**How it works**:
1. Query the experiment backend for ALL runs (including deleted/archived)
2. Query for ACTIVE/FINISHED runs only
3. Compare counts: `deleted_count = all_count - active_count`

**Pass condition**: `deleted_count == 0`

**Fail output**:
```
[FAIL] Deleted Runs: 3 runs deleted out of 15 total. NEVER delete runs.
```

**Backend-specific queries**:
- MLflow: `search_runs(view_type=ViewType.ALL)` vs `search_runs(view_type=ViewType.ACTIVE_ONLY)`
- W&B: Check `run.state` for `crashed`, `killed`, then look for missing run IDs

---

## Check 2: Hold-out Count (R7)

**Rule enforced**: Hold-out evaluation is a ONE-SHOT event. At most 1 run may be tagged as hold-out.

**How it works**:
1. Filter runs by tag `holdout=true` or `phase=holdout`
2. Count matching runs

**Pass condition**: `holdout_count <= 1`

**Fail output**:
```
[FAIL] Hold-out Count: 3 hold-out runs found. Hold-out is ONE-SHOT (max 1 run).
```

**Fix procedure**:
1. Identify which hold-out run is the legitimate one (first chronologically)
2. Re-tag extra runs as `phase=exploratory_holdout` (do NOT delete)
3. Document in 00_HYPOTHESES.md Deviation Log

---

## Check 3: Gate Conditions (R7)

**Rule enforced**: Hold-out evaluation must only happen AFTER CV gate conditions are met.

**How it works**:
1. Find the hold-out run (if any)
2. Find CV runs with gate metrics logged
3. Verify at least one CV run meets the gate threshold BEFORE the hold-out run timestamp
4. Gate thresholds are read from `docs/specs/02_METRICS.md`

**Pass condition**: No hold-out run exists OR a CV run meeting gate conditions precedes it.

**Fail output**:
```
[FAIL] Gate Conditions: Hold-out run at 2024-01-15 but no CV run meets gate (AUC >= 0.80) before that date.
```

**Fix procedure**:
1. If hold-out was premature: tag as `phase=exploratory_holdout`, re-run CV
2. If gate threshold needs revision: update `02_METRICS.md`, record deviation
3. Never re-run hold-out after peeking at results

---

## Check 4: Pre-Registration Timing (R9)

**Rule enforced**: Hypotheses must be committed to git BEFORE the first experiment run.

**How it works**:
1. Get the git timestamp of `docs/specs/00_HYPOTHESES.md` (first commit)
2. Get the start timestamp of the earliest experiment run
3. Compare: hypothesis commit must precede first run

**Pass condition**: `hypothesis_timestamp < first_run_timestamp`

**Fail output**:
```
[FAIL] Pre-Registration: First run at 2024-01-10 but 00_HYPOTHESES.md committed at 2024-01-12.
```

**Fix procedure**:
1. If hypotheses were written but not committed: this is a process issue, fix workflow
2. If hypotheses were written AFTER experiments: label ALL results as EXPLORATORY
3. Add a new pre-registration for any future confirmatory work

---

## Check 5: Spec Drift (R9)

**Rule enforced**: Specification documents must not change after experiments begin without logging deviations.

**How it works**:
1. Get git log for `docs/specs/*.md` files
2. Get the start timestamp of the first experiment run
3. Identify spec changes that occurred AFTER the first run
4. Check if those changes are recorded in the Deviation Log of `00_HYPOTHESES.md`

**Pass condition**: No post-experiment spec changes, OR all changes are logged in Deviation Log.

**Fail output**:
```
[FAIL] Spec Drift: 02_METRICS.md changed at 2024-01-20 (after first run at 2024-01-10) but not in Deviation Log.
```

**Fix procedure**:
1. Add an entry to the Deviation Log in `00_HYPOTHESES.md` for each undocumented change
2. Include: date, what changed, rationale, impact on confirmatory status
3. Mark affected results as exploratory if the change alters the analysis plan

---

## Exit Code Summary

| Scenario | Exit Code |
|----------|-----------|
| All 5 checks pass | 0 |
| Any check fails | 1 |
| Backend connection failure | 1 |
| Missing required files | 1 |
