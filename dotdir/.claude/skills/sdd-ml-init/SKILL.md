---
name: sdd-ml-init
description: >
  Initialize a Specification-Driven Development (SDD) directory structure for machine learning
  and data analysis projects with built-in anti-p-hacking safeguards. Interviews the user to
  collect project-specific requirements (features, split policy, metrics, hypotheses, experiment
  tools), then generates a complete project scaffold with CLAUDE.md prime rules (including
  anti-sycophancy and pre-registration directives), machine-readable schemas
  (feature_availability.yaml, Pandera validation, leakage checker), specification documents
  (hypothesis pre-registration, metrics with multiple comparison correction, split policy),
  and experiment configuration.
  Use when: (1) starting a new ML/data science project, (2) user says "init ML project",
  "create ML scaffold", "new data analysis project", (3) setting up leakage-proof ML pipelines,
  (4) any request to create a project structure with AI safety guardrails for ML experiments.
---

# SDD ML Project Initializer

Initialize a leakage-proof, p-hacking-resistant, specification-driven ML project through a structured interview.

## Workflow

1. **Interview** the user (2 rounds via AskUserQuestion)
2. **Create** directory structure (run `scripts/init_structure.py`)
3. **Generate** all project files from templates
4. **Run** integrity checks (run `scripts/leakage_check.py`)
5. **Verify** generated structure

## Step 1: Interview

Read [references/interview_guide.md](references/interview_guide.md) for the full question set.

**Round 1** (single AskUserQuestion, 4 questions):
- Project name + task type (classification/regression/multi-task)
- Data modality + subject grouping field + constraints
- Experiment tool (Hydra+MLflow / W&B / Neptune / Custom)
- Compliance level (medical / research / minimal)

**Round 2** (up to 4 targeted questions based on Round 1):
- Feature lists (inference_available vs inference_unavailable)
- Split policy (CV strategy, hold-out strategy)
- Metrics, gate thresholds, and multiple comparison correction needs
- Primary hypothesis and analysis plan (for pre-registration)

After interview, summarize all answers in a table and confirm before generating.

## Step 2: Create Directory Structure

Run the init script:

```bash
python scripts/init_structure.py <project-dir>
```

This creates:

```
project-root/
├── CLAUDE.md
├── docs/specs/
├── src/schema/
├── src/features/
├── src/models/
├── conf/
├── data/raw/
├── data/processed/
└── notebooks/
```

## Step 3: Generate Files

Generate files in this order. Read the corresponding reference for each template.

### 3a. Prime Rules (CLAUDE.md)

Read [references/prime_rules.md](references/prime_rules.md). Generate `CLAUDE.md` with 10 prime directives:
- Rules 1-7: Technical safeguards (routing, immutability, leakage, validation, tracking, split, gate)
- Rule 8: **Anti-Sycophancy** — report ALL results including unfavorable ones, never suppress contradictory findings
- Rule 9: **Pre-Registration** — record hypotheses before experiments, label post-hoc findings as exploratory
- Rule 10: **Full Reporting** — disclose total run count, deviations from plan, multiple comparison corrections

### 3b. Pre-Registration (docs/specs/00_HYPOTHESES.md)

Read [references/spec_templates.md](references/spec_templates.md) section "00_HYPOTHESES.md". Generate with:
- Primary and secondary hypotheses
- Exploratory vs confirmatory phase separation
- Deviation log table

### 3c. Machine-Readable Schemas (src/schema/)

Read [references/schema_templates.md](references/schema_templates.md). Generate:
- `src/schema/feature_availability.yaml` — inference_available and inference_unavailable feature lists
- `src/schema/data_validation.py` — Pandera schema with subject ID, feature columns, and value range checks

### 3d. Specification Documents (docs/specs/)

Read [references/spec_templates.md](references/spec_templates.md). Generate:
- `docs/specs/05_SPLIT_POLICY.md` — split unit, grouping constraints, CV and hold-out strategy
- `docs/specs/02_METRICS.md` — metrics, calibration, gate conditions, **multiple comparison correction rules**, hold-out one-shot protocol, reporting checklist
- `docs/specs/01_DATA_DICTIONARY.md` — variable catalog, imputation rules, encoding
- `docs/specs/04_COMPLIANCE.md` — only if compliance_level is "medical" or "research"

### 3e. Experiment Configuration (conf/)

Read [references/experiment_config.md](references/experiment_config.md). Generate:
- `conf/config.yaml` — main Hydra config (or W&B variant)
- `conf/model/baseline.yaml` — baseline model config
- `conf/features/default.yaml` — feature set definition
- `conf/split/group_kfold.yaml` — split configuration

### 3f. Data Access Layer and Enforcement (src/)

From [references/experiment_config.md](references/experiment_config.md), generate:
- `src/data_access.py` — centralized read-only raw data access

Copy `scripts/leakage_check.py` to `src/schema/leakage_check.py` for runtime enforcement.

## Step 4: Run Integrity Checks

After generation, run leakage_check.py if a feature matrix or split index already exists:

```bash
python src/schema/leakage_check.py \
    --schema src/schema/feature_availability.yaml \
    --features data/processed/feature_matrix.parquet \
    --split data/processed/split_index.json \
    --subject-col {{subject_id_field}}
```

## Step 5: Verify

After generation, verify:
- [ ] `feature_availability.yaml` lists match interview answers
- [ ] `CLAUDE.md` contains all 10 prime directives (including anti-sycophancy, pre-registration, full reporting)
- [ ] `00_HYPOTHESES.md` has primary hypothesis and exploratory/confirmatory phase separation
- [ ] `02_METRICS.md` has multiple comparison correction section and reporting checklist
- [ ] Split policy matches subject ID field and constraints
- [ ] Gate thresholds match agreed values
- [ ] No `04_COMPLIANCE.md` generated if compliance_level is "minimal"
- [ ] `leakage_check.py` is present in `src/schema/`

Print the final directory tree and confirm completion.
