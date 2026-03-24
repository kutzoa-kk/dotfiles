---
name: sdd-ml-experiment
description: >
  Initialize a phase-gated ML experiment environment with built-in TDD infrastructure,
  leakage prevention, and specification-driven safeguards. Extends sdd-ml-init with
  Phase A/B/C experiment progression (each phase has gate conditions that must pass
  before advancing), per-phase run scripts, pytest fixtures, and Polars-first data pipelines.
  Use when: (1) starting a new ML experiment within an existing or new project,
  (2) user says "new experiment", "create experiment", "init experiment",
  "set up ML experiment", "add experiment to project", (3) creating a phase-gated
  ML pipeline with validation → prediction → holdout evaluation stages,
  (4) any request involving experiment setup with anti-leakage and anti-p-hacking safeguards.
  This skill should be used even when the user just mentions wanting to "try a new model"
  or "test a hypothesis" — those are experiments that benefit from proper scaffolding.
---

# SDD ML Experiment Initializer

Set up a phase-gated, leakage-proof ML experiment with TDD infrastructure through a structured interview.

This skill builds on the conventions established by `sdd-ml-init` and adds:
- **Phase-based progression** (A → B → C) with explicit gate conditions
- **Per-phase run scripts** and evaluator modules
- **Test infrastructure** (conftest.py, pytest.ini, test templates)
- **Polars-first** data processing templates
- **Feature engineering patterns** (builder + aggregator)

## Prerequisites

If the project has NOT been initialized with `sdd-ml-init`, run that first.
If it has, this skill creates a new experiment directory inside the existing project.

## Workflow

1. **Detect Context** — check if sdd-ml-init scaffold exists
2. **Interview** the user (2 rounds)
3. **Create** experiment directory structure
4. **Generate** all experiment files from templates
5. **Generate** test infrastructure
6. **Run** integrity checks
7. **Verify** generated structure

## Step 1: Detect Context

Check the current project for sdd-ml-init artifacts:

```
project-root/
├── CLAUDE.md              ← exists? (sdd-ml-init was run)
├── src/schema/
│   └── feature_availability.yaml  ← exists?
└── docs/specs/
    └── 00_HYPOTHESES.md   ← exists?
```

**If sdd-ml-init artifacts exist**: Skip project-level generation, focus on experiment directory.
**If not**: Suggest running sdd-ml-init first, or offer to generate project-level files inline.

## Step 2: Interview

Read [references/experiment_interview.md](references/experiment_interview.md) for the full question set.

**Round 1** (single AskUserQuestion, up to 4 questions):
- Experiment name + location in project tree (e.g., `code/gcrs/kknb/exp002`)
- Prediction target + task type (regression / classification / multi-task)
- Phase structure: how many phases? What does each validate?
- Data sources: what raw data feeds this experiment?

**Round 2** (up to 4 targeted questions):
- Feature engineering: builder pattern, aggregation needs
- Model candidates + hyperparameter strategy
- Phase-specific gate conditions (metric + threshold per phase)
- Holdout protocol (one-shot? temporal? facility-based?)

After interview, summarize all answers in a table and confirm before generating.

## Step 3: Create Experiment Directory

Run the init script or create manually:

```
experiment-root/           # e.g., code/gcrs/kknb/exp002
├── CLAUDE.md              # Experiment-specific prime directives
├── conf/
│   ├── config.yaml        # Main Hydra config
│   ├── model/             # Model configs per phase
│   ├── features/          # Feature set definitions
│   └── split/             # Split strategy configs
├── src/
│   ├── data_access.py     # Centralized data loading
│   ├── split_generator.py # Split creation + validation
│   ├── features/          # Feature engineering
│   │   ├── __init__.py
│   │   └── feature_matrix_builder.py
│   ├── models/            # Phase evaluators + trainers
│   │   ├── __init__.py
│   │   ├── phase_a_evaluator.py
│   │   ├── phase_b_evaluator.py
│   │   └── direction_trainer.py  (or relevant trainer)
│   ├── analysis/          # Post-hoc analysis modules
│   │   └── __init__.py
│   └── schema/
│       ├── feature_availability.yaml
│       ├── data_validation.py
│       └── leakage_check.py
├── scripts/               # Phase run scripts
│   ├── run_phase_a.py
│   ├── run_phase_b.py
│   └── run_phase_c.py
├── tests/                 # Test infrastructure
│   ├── conftest.py        # Shared fixtures
│   └── test_*.py          # Per-module tests
├── data/
│   ├── raw/               # Read-only external data
│   └── processed/         # Generated artifacts
├── docs/
│   ├── specs/             # Pre-registered specs
│   │   ├── 00_HYPOTHESES.md
│   │   ├── 01_DATA_DICTIONARY.md
│   │   ├── 02_METRICS.md
│   │   └── 05_SPLIT_POLICY.md
│   └── experiments/       # Experiment reports
├── notebooks/             # EDA only (no implementation)
├── conftest.py            # Root pytest config
└── pytest.ini             # pytest settings
```

## Step 4: Generate Experiment Files

Generate files in this order. Read the corresponding reference for each template.

### 4a. Experiment CLAUDE.md

Read [references/experiment_prime_rules.md](references/experiment_prime_rules.md).

Generate experiment-level CLAUDE.md with 10 prime directives (same structure as sdd-ml-init)
plus experiment-specific additions:
- Phase progression rules (which phases exist, gate conditions)
- Data source paths
- Feature engineering constraints

### 4b. Phase Run Scripts

Read [references/phase_scripts.md](references/phase_scripts.md).

Generate a `scripts/run_phase_X.py` for each phase. Each script:
- Loads config via Hydra
- Runs the phase evaluator/trainer
- Checks gate conditions
- Logs results to MLflow
- Prints PASS/FAIL verdict

### 4c. Phase Evaluators and Trainers

Read [references/model_templates.md](references/model_templates.md).

Generate evaluator/trainer modules in `src/models/`:
- **Phase A evaluator**: Validates score construction, internal consistency, batch effects
- **Phase B evaluator**: Runs CV training, evaluates prediction performance
- **Phase C evaluator**: One-shot holdout evaluation (gated by Phase B pass)
- **Trainer**: Model training with CV, feature importance, OOF predictions

### 4d. Feature Engineering

Read [references/feature_templates.md](references/feature_templates.md).

Generate feature modules in `src/features/`:
- **feature_matrix_builder.py**: Combines data sources into training matrix
- Additional builders as needed (e.g., step_aggregator for time-series)

### 4e. Schema and Validation

Reuse sdd-ml-init templates (feature_availability.yaml, data_validation.py, leakage_check.py)
with Polars-compatible validation where appropriate.

### 4f. Specification Documents

Reuse sdd-ml-init spec templates (00_HYPOTHESES.md, 02_METRICS.md, 05_SPLIT_POLICY.md)
with phase-specific gate conditions added to 02_METRICS.md.

### 4g. Hydra Configuration

Read [references/hydra_config.md](references/hydra_config.md).

Generate Hydra configs adapted to the experiment's phase structure.

## Step 5: Generate Test Infrastructure

Read [references/test_templates.md](references/test_templates.md).

This is a key differentiator from sdd-ml-init. Generate:

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### conftest.py (root)
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
```

### tests/conftest.py
Shared fixtures providing:
- Minimal synthetic datasets (Polars DataFrames)
- Mock config objects (OmegaConf DictConfig)
- Temporary directories for outputs
- Feature availability schema fixtures

### Test stubs for each generated module
For every `src/**/*.py` file generated, create a corresponding `tests/test_*.py` with:
- At least one test class
- Fixture-based setup
- Placeholder test that asserts the module is importable

The test stubs follow the TDD pattern — they should be written to FAIL initially,
guiding the user to implement the actual logic.

## Step 6: Run Integrity Checks

After generation:

1. Run `python -m pytest tests/ --collect-only` to verify test discovery
2. Run leakage_check.py if feature schema exists
3. Verify all generated files are syntactically valid Python

## Step 7: Verify

After generation, verify:
- [ ] Experiment directory matches the expected structure
- [ ] CLAUDE.md contains all 10 prime directives + phase rules
- [ ] Phase run scripts exist for each defined phase
- [ ] Test files exist for each src module
- [ ] feature_availability.yaml matches interview answers
- [ ] Gate conditions in 02_METRICS.md match interview answers
- [ ] pytest.ini and conftest.py are in place
- [ ] `pytest --collect-only` discovers all test files

Print the final directory tree, test collection output, and confirm completion.

## Design Principles

These principles guide the templates — understanding them helps when adapting to edge cases.

### Phase Gates Prevent P-Hacking
Each phase must pass its gate conditions before the next phase begins.
This prevents the common pattern of "trying everything until something works on holdout."

### One Module, One Responsibility
Each src module does exactly one thing. Evaluators evaluate, trainers train,
builders build feature matrices. This makes testing straightforward and prevents
god-objects that are hard to debug.

### Polars Over Pandas
Templates default to Polars for data processing. Polars is immutable by default,
which aligns with the no-mutation principle and prevents accidental data corruption.
Exception: Pandera schemas use pandas (Pandera doesn't support Polars natively yet).

### Tests As Documentation
The generated test stubs serve as executable documentation of expected behavior.
When a new team member reads `test_phase_a_evaluator.py`, they immediately understand
what Phase A is supposed to do.
