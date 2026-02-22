---
name: sdd-pre-train-guard
description: >
  Run 5 automated pre-training checks that enforce SDD prime rules R3 (Leakage Prevention),
  R4 (Validation), and R6 (Split Integrity) before any model training begins.
  Checks: (1) feature leakage via feature_availability.yaml, (2) split policy consistency
  between docs/specs/05_SPLIT_POLICY.md and training code, (3) preprocessing inside folds
  via AST analysis, (4) validation artifact existence, (5) feature schema validity.
  Use when: (1) before running model training, (2) user says "check before training",
  "pre-train guard", "leakage check", (3) CI/CD gate before training step,
  (4) any request to verify ML pipeline integrity before training.
---

# SDD Pre-Train Guard

Run 5 automated checks before training to prevent data leakage, split violations, and missing validation artifacts.

## Workflow

1. **Identify** the project directory and training script
2. **Run** pre-train guard checks (`scripts/pre_train_guard.py`)
3. **Review** results and fix any failures
4. **Verify** all checks pass before proceeding to training

## Step 1: Identify Project Context

Determine the following from the user or project structure:

- **Project directory**: Root of the SDD ML project (contains `src/`, `docs/`, `data/`)
- **Training script**: Path to the main training script (e.g., `src/models/train.py`)
- **Subject column**: Name of the subject ID column (default: `subject_id`)

If the project was initialized with `sdd-ml-init`, these paths follow the standard structure.

## Step 2: Run Pre-Train Guard

Read [references/check_definitions.md](references/check_definitions.md) for detailed check definitions.

Run the guard script:

```bash
python scripts/pre_train_guard.py \
    --project-dir <project-root> \
    --training-script <path/to/train.py> \
    --subject-col <subject_id_field>
```

The script runs 5 checks in order:

| # | Check | Rule | What it detects |
|---|-------|------|-----------------|
| 1 | Feature Schema | R3, R4 | Missing or invalid feature_availability.yaml |
| 2 | Feature Leakage | R3 | Forbidden features in training data/code |
| 3 | Split Policy | R6 | Mismatch between spec and code splitter |
| 4 | Preprocessing in Folds | R3, R4 | .fit() calls outside Pipeline context |
| 5 | Validation Artifact | R4 | Missing or failed validation_report.json |

## Step 3: Handle Failures

For each failed check, follow the fix procedure in [references/check_definitions.md](references/check_definitions.md).

Common fixes:

- **Feature Leakage**: Remove leaked columns or update `feature_availability.yaml`
- **Split Policy**: Update splitter in code or update `05_SPLIT_POLICY.md` (record deviation)
- **Preprocessing**: Wrap preprocessors in `sklearn.pipeline.Pipeline`
- **Validation Artifact**: Run `python src/schema/data_validation.py` to generate report
- **Feature Schema**: Run `sdd-ml-init` or manually create `feature_availability.yaml`

After fixing, re-run the guard to confirm all checks pass.

## Step 4: Integration

Read [references/integration_guide.md](references/integration_guide.md) for permanent integration options:

- **Hydra callback**: Auto-run before each training job
- **pytest fixture**: Block CI on guard failures
- **Makefile target**: `make train` depends on `make guard`

Copy the guard script to the target project:

```bash
cp scripts/pre_train_guard.py <project>/src/schema/pre_train_guard.py
```

## Verification Checklist

- [ ] All 5 checks return `[PASS]`
- [ ] `feature_availability.yaml` exists and has non-empty `inference_available`
- [ ] No `.fit()` calls outside Pipeline context in training script
- [ ] `validation_report.json` exists with all checks passed
- [ ] Split policy in code matches `05_SPLIT_POLICY.md`
- [ ] Guard script copied to target project's `src/schema/`
- [ ] Integration method chosen and configured (Hydra/pytest/Makefile)

Print final report and confirm all checks pass before proceeding to training.
