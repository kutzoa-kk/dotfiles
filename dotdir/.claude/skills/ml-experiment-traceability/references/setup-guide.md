# Setup Guide — MLflow + DVC Experiment Traceability Foundation

Step-by-step. Replace `<series>` with the chosen base dir (e.g. `code/kknb/2.1.0`, `experiments`, `src/ml`). Commands assume `uv`; for plain venvs swap `uv add X` → `pip install X` and `uv run Y` → `.venv/bin/Y`. All code referenced here lives in `references/templates.md`.

## 0. Prerequisites
- A git repository (`git rev-parse --show-toplevel` works).
- Python ≥ 3.10, `uv` (or a `.venv` + pip).
- A DataFrame library — templates use `polars`; adapt to `pandas` if that is the repo's convention.

## 1. Dependencies
```bash
uv add mlflow pandera dvc        # or: pip install mlflow "pandera>=0.20" dvc
uv add polars                    # if not already present
```
Verify:
```bash
uv run python -c "import mlflow, polars; import pandera.polars as pa; print('ok', mlflow.__version__)"
uv run dvc --version
```
Notes:
- If the venv has no `python -m pip` (uv-managed), install with `uv add` / `uv pip install <pkg> --python .venv/bin/python`.
- `pandera>=0.20` is required for the `pandera.polars` API.

## 2. Series package skeleton
Create (contents in templates.md):
- `<series>/common/__init__.py` (empty)
- `<series>/tests/__init__.py` (empty)
- `<series>/conftest.py` — puts `<series>/` on `sys.path` so `from common import ...` resolves under pytest.
- `<series>/pytest.ini` — `import-mode=importlib` (lets each exp's same-named test files coexist).

Sanity: `uv run pytest <series>/tests -q` → `no tests ran` (exit 5) is expected and fine at this point.

## 3. MLflow backend
No server needed. The `common/tracking.py` helper points the tracking URI at a SQLite file under the series dir: `sqlite:///<series>/mlflow.db`, with artifacts in `<series>/mlruns/`. Both are gitignored (Step 5). `mlflow ui --backend-store-uri sqlite:///$(pwd)/<series>/mlflow.db` opens the run comparison UI.

## 4. DVC init + local remote (repo root)
```bash
cd "$(git rev-parse --show-toplevel)"
uv run dvc init                                        # creates .dvc/ (+ .dvc/.gitignore excluding /cache) and .dvcignore; auto-git-adds them
mkdir -p ~/dvc-storage/<repo-name>
uv run dvc remote add -d local ~/dvc-storage/<repo-name>
uv run dvc remote list                                 # expect: local  <abspath>  (default)
```
- The `-d` makes `local` the default remote. Its absolute path lands in `.dvc/config` (fine for single-dev; for multi-machine use `dvc remote add --local`, which writes the git-ignored `.dvc/config.local`).
- Commit ONLY: `.dvc/config .dvc/.gitignore .dvcignore pyproject.toml`. Never commit `.dvc/cache`, `uv.lock` (usually gitignored), or data.

## 5. .gitignore
Ensure these are ignored (add if missing):
```gitignore
mlflow.db
mlruns/
*.parquet
*.csv
```
`dvc init` already adds `/cache` inside `.dvc/.gitignore`. Do NOT gitignore `dvc.yaml`/`dvc.lock`/`.dvc/config` — those pointers MUST be tracked (they are what pins data versions to git).

## 6. Create the foundation code
From `references/templates.md`, create each file at its target path under `<series>/` (and `docs/adr/` at repo root):
- `common/`: `tracking.py`, `splits.py`, `leakage_check.py`, `validation.py`, `dvc_link.py`
- `specs/`: `hypotheses.md`, `metrics.md`, `split_policy.md`, `feature_availability.yaml`
- `_template/`: `README.md`, `conf/config.yaml`, `scripts/10_build_master_table.py`, `scripts/20_build_x_vector.py`, `src/__init__.py`, `outputs/.gitkeep`, `tests/test_smoke.py`, `dvc.yaml`
- `scripts/new_exp.py`
- `docs/adr/`: `README.md`, `0000-template.md` (+ record the setup decisions as `0001..`)

Build each `common/` module test-first (TDD) — the test bodies are in templates.md. Run tests per module as you go: `uv run pytest <series>/tests/test_<mod>.py -q`.

## 7. Verification gate (all must pass)
```bash
uv run pytest <series> -q                              # all tests green
uv run ruff check <series>                             # clean (run over the WHOLE series, not per-file)
uv run dvc remote list                                 # local (default)
# dummy MLflow run proves the backend works end-to-end:
uv run python -c "
import sys; sys.path.insert(0, '<series>')
from common import tracking
from common.splits import make_subject_split
import polars as pl
df = pl.DataFrame({'subject_id':['s1','s2','s3'],'location':['A','A','B'],'is_aeon_holdout':[False,False,True]})
split = make_subject_split(df, seed=42)
with tracking.start_run('exp/smoke', {'seed':42}):
    tracking.log_split_metadata(split); tracking.log_metrics({'dummy':1.0})
print('mlflow run recorded')
"
ls <series>/mlflow.db                                  # exists (gitignored)
```

## 8. Using it (per experiment)
```bash
uv run python <series>/scripts/new_exp.py --name exp001_master_table   # clone _template
cd <series>/exp001_master_table
uv run dvc repro                                       # run the pipeline stages, write dvc.lock (git-track it)
uv run dvc push                                        # push data blobs to the remote
```
Inside a run, call `common.dvc_link.log_dvc_versions(exp_dir)` to tag the run with the data hashes.

## Gotchas (each cost a real debugging cycle)
1. **sys.path off-by-one**: a template script at `<series>/<exp>/scripts/x.py` must add `parents[2]` (the series dir) to `sys.path`, not `parents[3]`. `parents[3]` is one level too high → `ModuleNotFoundError: common`.
2. **Test-file name collisions**: without `import-mode=importlib`, two exps each carrying `tests/test_smoke.py` crash pytest collection ("import file mismatch"). The `pytest.ini` fixes it.
3. **`dvc.lock` hash field**: `out["hash"]` is the algorithm name (`"md5"`/`"sha256"`), not the value. The value is under a key named by the algo. Extract: `out.get("md5") or out.get(out.get("hash",""), "")`.
4. **`outputs/.gitkeep` is gitignored** when `outputs/` matches a gitignore rule — so it will not be committed and a fresh checkout's template lacks it. Have `new_exp.py` `mkdir(exist_ok=True)` the `outputs/` dir so generated exps always have it.
5. **Per-file lint hides debt**: `ruff check <one file>` on the module skips the test file committed alongside it. Lint the whole series dir so `test_*.py` import-order issues surface before commit.
6. **MLflow tracking URI must be set per call** (inside `start_run`), reading the module-level DB path at call time — otherwise tests that redirect the DB (monkeypatch) write to the real backend.
7. **Commit hygiene for a data tool**: never `git add -A` — DVC cache, generated exps, `mlflow.db`, and data blobs must stay out of git. Add explicit paths only.
