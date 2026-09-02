---
name: ml-experiment-traceability
description: Set up an MLflow + DVC experiment-traceability foundation in a Python ML project — MLflow run tracking (SQLite backend), DVC data/pipeline versioning with a local remote, a dvc_link that ties each run to its exact data version, leakage-proof subject/site/group splits with an assertion-based leakage checker, an exp scaffold (template + generator), Pandera validation, SDD pre-registration specs, and an ADR base. Use when the user wants reproducible ML experiments, experiment tracking plus data versioning, "MLflow and DVC", a leakage-proof split/experiment setup, or an ADR/traceability foundation for an ML repo. Do NOT use for training or tuning a specific model — this builds the environment the experiments run in, not the model.
---

# ML Experiment Traceability Foundation (MLflow + DVC)

Builds a portable, leakage-proof experiment environment where every run is reproducible. **MLflow** tracks runs/params/metrics; **DVC** versions data + pipelines; a thin `dvc_link` ties each run to its exact data version. Reproducibility rests on git: a committed `dvc.lock` + the run's `git_sha` pin **run ⇔ data ⇔ code**.

Distilled from a production build (design → ADR → plan → TDD → review). Generalize the paths to the target repo; the templates carry the working logic.

## When to use
- "set up MLflow and DVC", "experiment tracking + data versioning", "reproducible ML pipeline"
- "leakage-proof splits", "subject/site holdout", "experiment scaffold", "ADR for ML decisions"
- Starting a new ML experiment series that must be traceable and reproducible.

## When NOT to use
- Training/tuning a specific model (this builds the environment, not the model).
- A non-Python or non-ML repo.

## Core idea — why this shape
- **MLflow** = run tracking (params/metrics/artifacts, SQLite backend, `mlflow ui` run comparison). Weak at versioning large data.
- **DVC** = data + pipeline versioning (`dvc.yaml`/`dvc repro`, small `.dvc`/`dvc.lock` pointers in git, data blobs in a cache/remote). Weak at metrics.
- **Linkage (loose)** = the run logs `git_sha`; the committed `dvc.lock` pins the data. So a run is fully reproducible via `git checkout <sha> && dvc checkout`. `dvc_link` additionally logs data hashes as MLflow tags for UI visibility — a convenience layer, not the reproducibility mechanism.
- **Leakage-proof by construction** = splits are subject/site/holdout group-aware; `leakage_check` raises `AssertionError` if a subject crosses train/test or a holdout row leaks into train. Bad splits fail at runtime, never silently.

## Setup workflow
1. **Pick a series base dir** (e.g. `code/<series>/`, `experiments/`, `src/ml/`). Everything below lives under it, EXCEPT `dvc init` (repo root) and ADRs (`docs/adr/` at repo root).
2. **Follow `references/setup-guide.md`** — dependencies, MLflow backend, `dvc init` + local remote, `.gitignore`, pytest config, and the verification gate.
3. **Create the code from `references/templates.md`** — `common/` (tracking, splits, leakage_check, validation, dvc_link), `conftest.py`, `pytest.ini`, `_template/` + `scripts/new_exp.py`, `specs/`, and `docs/adr/`.
4. **Verify** — all tests green, a dummy MLflow run recorded, `dvc remote list` shows the remote.

## Architecture (portable layout)
```
<repo root>/
  .dvc/  .dvcignore                    # dvc init (repo-root; .dvc/cache gitignored)
  docs/adr/                            # ADR base: 0000-template.md + decision records
  <series>/                            # e.g. code/kknb/2.1.0 or experiments/
    common/  tracking.py  splits.py  leakage_check.py  validation.py  dvc_link.py  __init__.py
    specs/   hypotheses.md  metrics.md  split_policy.md  feature_availability.yaml
    _template/   conf/config.yaml  scripts/10_*.py 20_*.py  src/  tests/test_smoke.py  dvc.yaml
    scripts/new_exp.py                 # generates <expNNN> from _template
    conftest.py   pytest.ini
    mlflow.db   mlruns/                # gitignored
    <expNNN>/                          # a generated experiment
```

## Conventions (baked into the templates)
- **Run via `uv run`** (`uv run pytest`, `uv run python`, `uv run dvc ...`); `.venv/bin/` direct calls also work.
- **Fail-fast, no silent fallbacks**: validation → `pandera.errors.SchemaError`; leakage → `AssertionError`; git-sha failure → `RuntimeError`; corrupt `dvc.lock` → `yaml.YAMLError`.
- **MLflow naming**: experiment = `<series>/expNNN_<topic>`; run = `<YYYYMMDD-HHMMSS>_<git_sha7>`. Always log split metadata + seed + git_sha.
- **pytest**: `pytest.ini` sets `import-mode=importlib` so each exp's same-named test files (e.g. `test_smoke.py`) coexist without collision.
- **Data hygiene**: `*.parquet/*.csv` stay gitignored; DVC pointers (`dvc.yaml`/`dvc.lock`/`.dvc/config`) ARE tracked; the DVC cache is never committed.
- **Governance**: significant decisions → `docs/adr/` (one file per decision, Status/Context/Decision/Consequences/Alternatives/References).

## Common pitfalls (learned the hard way)
- **sys.path depth in template scripts** must reach the series dir (where `common/` lives) — off-by-one gives `ModuleNotFoundError`. Template scripts are at `<series>/<exp>/scripts/x.py` → `parents[2]` is the series dir. `conftest.py` at the series root handles pytest's path; scripts self-insert for standalone runs.
- **Same-named test files collide** under pytest's default prepend import mode once you have >1 exp — `import-mode=importlib` fixes it.
- **`dvc.lock` `hash` field is the ALGO NAME** (md5/sha256), not the value; read the value via `out.get("md5") or out.get(out.get("hash",""), "")`.
- **The exp `outputs/` dir**: a `.gitkeep` there is often gitignored (if `outputs/` is ignored), so have the generator `mkdir` it rather than relying on a tracked `.gitkeep`.
- **Per-file lint misses test files**: run lint over the whole series dir, not just the module you changed, or the test files accumulate `I001`/`F401`.

## References
- `references/setup-guide.md` — step-by-step setup, the verification gate, and gotchas.
- `references/templates.md` — every code/config template (generalized), organized by file with its target path.
