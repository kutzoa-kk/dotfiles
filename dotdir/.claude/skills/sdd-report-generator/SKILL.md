---
name: sdd-report-generator
description: >
  Generate a comprehensive final experiment report (docs/FINAL_REPORT.md) from collected
  experiment runs. Enforces R8 (Anti-Sycophancy: report ALL results including unfavorable)
  and R10 (Full Reporting: disclose total run count, deviations, multiple comparison corrections).
  Collects runs from MLflow/W&B/local, parses hypotheses from 00_HYPOTHESES.md, applies
  Bonferroni or BH-FDR corrections, includes deviation log, and adds anti-sycophancy declaration.
  Use when: (1) experiments are complete and ready for reporting, (2) user says "generate report",
  "final report", "write up results", (3) preparing manuscript or presentation with experiment
  results, (4) any request to summarize ML experiment outcomes.
---

# SDD Report Generator

Generate a complete, anti-sycophantic final report from experiment runs with multiple comparison corrections and full disclosure.

## Workflow

1. **Collect** experiment runs (`scripts/collect_runs.py`)
2. **Generate** final report (`scripts/generate_report.py`)
3. **Review** report for completeness
4. **Verify** anti-sycophancy and full reporting compliance

## Step 1: Collect Runs

Collect all runs (including deleted and failed) from the experiment backend:

```bash
python scripts/collect_runs.py \
    --project-dir <project-root> \
    --backend <mlflow|wandb|local> \
    [backend-specific args] \
    --output data/processed/all_runs.json
```

Backend arguments:

| Backend | Required Arguments |
|---------|-------------------|
| MLflow | `--tracking-uri <URI> --experiment-name <NAME>` |
| W&B | `--entity <TEAM> --wandb-project <PROJECT>` |
| Local | `--runs-dir <PATH>` (default: `data/processed/runs/`) |

Output: `data/processed/all_runs.json` containing all runs with summary statistics.

## Step 2: Generate Report

Read [references/report_template.md](references/report_template.md) for the report structure.
Read [references/correction_methods.md](references/correction_methods.md) for correction details.

```bash
python scripts/generate_report.py \
    --project-dir <project-root> \
    --runs-json data/processed/all_runs.json \
    --correction <bonferroni|bh-fdr> \
    --alpha 0.05 \
    --project-name "My Project"
```

The report includes 7 sections:

| # | Section | SDD Rule |
|---|---------|----------|
| 1 | Pre-Registered Hypotheses | R9 |
| 2 | Full Run Summary (ALL runs) | R10 |
| 3 | Gate Condition Results | R7 |
| 4 | Multiple Comparison Corrections | R10 |
| 5 | Deviation Log | R9 |
| 6 | Anti-Sycophancy Declaration | R8 |
| 7 | Reproducibility Info | R10 |

### Correction Method Selection

| Scenario | Method |
|----------|--------|
| ≤ 5 comparisons, medical/clinical | `bonferroni` |
| > 5 comparisons, exploratory | `bh-fdr` |
| Single comparison | No correction needed |

## Step 3: Review Report

After generation, review `docs/FINAL_REPORT.md` for:

- **Completeness**: All hypotheses have results (Confirmed / Not Confirmed / Exploratory / Inconclusive)
- **Accuracy**: Metrics match the collected runs
- **Gate conditions**: Correctly evaluated against spec thresholds
- **Corrections**: Applied when multiple comparisons exist
- **Deviations**: All entries from 00_HYPOTHESES.md are included

## Step 4: Verify

## Verification Checklist

- [ ] `all_runs.json` contains ALL runs (including deleted and failed)
- [ ] Report includes total run count and deleted count
- [ ] All pre-registered hypotheses have results
- [ ] Exploratory analyses are labeled as such
- [ ] Multiple comparison correction applied (if applicable)
- [ ] Raw AND adjusted p-values shown
- [ ] Deviation log included from 00_HYPOTHESES.md
- [ ] Anti-Sycophancy Declaration section present
- [ ] No results selectively omitted
- [ ] Gate condition pass/fail matches spec thresholds

Print report path and validation results.
