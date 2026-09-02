# Templates — all files (generalized)

Create each at its target path under `<series>/` (ADRs at repo-root `docs/adr/`). Paths are portable — the only assumption is that `common/` sits directly under `<series>/`. Build `common/` modules test-first; test bodies are included.

---

## `<series>/conftest.py`
```python
"""Puts the series dir on sys.path so `from common import ...` resolves under pytest."""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
```

## `<series>/pytest.ini`
```ini
[pytest]
# Each exp (and _template) may carry tests/test_smoke.py; prepend mode collides on the
# duplicate module name. importlib mode disambiguates by path so they coexist.
addopts = --import-mode=importlib
```

## `<series>/common/__init__.py`
Empty file.

---

## `<series>/common/splits.py`
```python
"""Group-aware subject/site/holdout split generation. train and test are always
subject-disjoint (for site/holdout too: test subjects are removed from train)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl


@dataclass(frozen=True)
class SplitSpec:
    seed: int
    strategy: str  # "subject" | "site" | "aeon"
    train_subjects: tuple[str, ...]
    test_subjects: tuple[str, ...]
    holdout_sites: tuple[str, ...] = ()
    aeon_locked: bool = False


def _require(df: pl.DataFrame, col: str) -> None:
    if col not in df.columns:
        raise ValueError(f"{col} column required")


def _all_subjects(df: pl.DataFrame) -> list[str]:
    _require(df, "subject_id")
    return sorted(df["subject_id"].unique().to_list())


def make_subject_split(df: pl.DataFrame, seed: int, test_frac: float = 0.2) -> SplitSpec:
    subs = np.array(_all_subjects(df))
    rng = np.random.default_rng(seed)
    perm = rng.permutation(subs)
    n_test = max(1, int(round(len(perm) * test_frac)))
    test = tuple(sorted(perm[:n_test].tolist()))
    train = tuple(sorted(perm[n_test:].tolist()))
    return SplitSpec(seed=seed, strategy="subject", train_subjects=train, test_subjects=test)


def _holdout_from_mask(df: pl.DataFrame, mask: pl.Expr) -> tuple[tuple[str, ...], tuple[str, ...]]:
    test_subjects = set(df.filter(mask)["subject_id"].to_list())
    all_subjects = set(_all_subjects(df))
    train_subjects = all_subjects - test_subjects
    return tuple(sorted(train_subjects)), tuple(sorted(test_subjects))


def make_site_holdout(df: pl.DataFrame, holdout_sites, seed: int = 0) -> SplitSpec:
    _require(df, "location")
    hs = tuple(sorted(set(holdout_sites)))
    train, test = _holdout_from_mask(df, pl.col("location").is_in(list(hs)))
    return SplitSpec(seed=seed, strategy="site", train_subjects=train, test_subjects=test, holdout_sites=hs)


def make_aeon_holdout(df: pl.DataFrame, seed: int = 0) -> SplitSpec:
    _require(df, "is_aeon_holdout")
    train, test = _holdout_from_mask(df, pl.col("is_aeon_holdout"))
    return SplitSpec(seed=seed, strategy="aeon", train_subjects=train, test_subjects=test, aeon_locked=True)
```
Test `<series>/tests/test_splits.py`:
```python
import polars as pl
import pytest

from common.splits import make_aeon_holdout, make_site_holdout, make_subject_split


def _df():
    return pl.DataFrame({
        "subject_id": ["s1", "s1", "s2", "s3", "s4", "s5"],
        "location": ["A", "A", "A", "B", "B", "C"],
        "is_aeon_holdout": [False, False, False, False, False, True],
    })


def test_subject_split_is_disjoint_by_subject():
    s = make_subject_split(_df(), seed=42, test_frac=0.4)
    assert set(s.train_subjects).isdisjoint(set(s.test_subjects))
    assert set(s.train_subjects) | set(s.test_subjects) == {"s1", "s2", "s3", "s4", "s5"}


def test_subject_split_is_deterministic_by_seed():
    assert make_subject_split(_df(), seed=7).test_subjects == make_subject_split(_df(), seed=7).test_subjects


def test_site_holdout_puts_site_subjects_in_test_only():
    s = make_site_holdout(_df(), holdout_sites=["C"], seed=0)
    assert "s5" in s.test_subjects and "s5" not in s.train_subjects
    assert set(s.train_subjects).isdisjoint(set(s.test_subjects))


def test_aeon_holdout_locks_all_aeon_subjects_to_test():
    s = make_aeon_holdout(_df(), seed=0)
    assert "s5" in s.test_subjects and "s5" not in s.train_subjects and s.aeon_locked is True


def test_missing_required_column_raises():
    with pytest.raises(ValueError):
        make_subject_split(pl.DataFrame({"location": ["A"]}), seed=1)
```

---

## `<series>/common/leakage_check.py`
```python
"""Assert no subject crosses train/test and no holdout row leaks into train (fail-fast)."""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from common.splits import SplitSpec


@dataclass(frozen=True)
class LeakageReport:
    subject_leak_ok: bool
    holdout_locked_ok: bool

    @property
    def ok(self) -> bool:
        return self.subject_leak_ok and self.holdout_locked_ok


def assert_no_subject_leak(train_df: pl.DataFrame, test_df: pl.DataFrame) -> None:
    overlap = set(train_df["subject_id"].to_list()) & set(test_df["subject_id"].to_list())
    assert not overlap, f"subject leak: {len(overlap)} in both splits: {sorted(overlap)[:5]}"


def assert_holdout_locked(df: pl.DataFrame, split: SplitSpec) -> None:
    train_rows = df.filter(pl.col("subject_id").is_in(list(split.train_subjects)))
    if split.aeon_locked:
        leaked = train_rows.filter(pl.col("is_aeon_holdout"))
        assert leaked.height == 0, f"aeon holdout leaked into train: {leaked.height} rows"
    if split.holdout_sites:
        leaked = train_rows.filter(pl.col("location").is_in(list(split.holdout_sites)))
        assert leaked.height == 0, f"holdout site leaked into train: {leaked.height} rows"


def run_all_checks(train_df: pl.DataFrame, test_df: pl.DataFrame, split: SplitSpec) -> LeakageReport:
    assert_no_subject_leak(train_df, test_df)
    full = pl.concat([train_df, test_df], how="vertical_relaxed")
    assert_holdout_locked(full, split)
    return LeakageReport(subject_leak_ok=True, holdout_locked_ok=True)
```
Test `<series>/tests/test_leakage_check.py`:
```python
import polars as pl
import pytest

from common.leakage_check import (
    LeakageReport, assert_holdout_locked, assert_no_subject_leak, run_all_checks)
from common.splits import SplitSpec


def test_no_subject_leak_raises_on_overlap():
    with pytest.raises(AssertionError):
        assert_no_subject_leak(pl.DataFrame({"subject_id": ["s1", "s2"]}),
                               pl.DataFrame({"subject_id": ["s2", "s3"]}))


def test_holdout_locked_raises_when_aeon_row_in_train():
    df = pl.DataFrame({"subject_id": ["s1"], "location": ["A"], "is_aeon_holdout": [True]})
    bad = SplitSpec(seed=0, strategy="aeon", train_subjects=("s1",), test_subjects=(), aeon_locked=True)
    with pytest.raises(AssertionError):
        assert_holdout_locked(df, bad)


def test_holdout_locked_raises_when_holdout_site_in_train():
    df = pl.DataFrame({"subject_id": ["s1"], "location": ["siteX"], "is_aeon_holdout": [False]})
    bad = SplitSpec(seed=0, strategy="site", train_subjects=("s1",), test_subjects=(), holdout_sites=("siteX",))
    with pytest.raises(AssertionError):
        assert_holdout_locked(df, bad)


def test_run_all_checks_returns_ok_report_when_clean():
    df = pl.DataFrame({"subject_id": ["s1", "s2"], "location": ["A", "B"], "is_aeon_holdout": [False, True]})
    train = df.filter(pl.col("subject_id") == "s1")
    test = df.filter(pl.col("subject_id") == "s2")
    split = SplitSpec(seed=0, strategy="aeon", train_subjects=("s1",), test_subjects=("s2",), aeon_locked=True)
    report = run_all_checks(train, test, split)
    assert isinstance(report, LeakageReport) and report.ok is True
```

---

## `<series>/common/validation.py`
Adapt the required columns to your domain — the keys below are examples (a "master table" of 1 row per session). `strict=False` allows extra columns; `coerce=False` makes a wrong dtype RAISE.
```python
"""Pandera(polars) schema for the analysis table. Fail-fast on missing/mistyped columns."""
from __future__ import annotations

import pandera.polars as pa
import polars as pl


class MasterTableSchema(pa.DataFrameModel):
    subject_id: str
    session_id: str
    year_month_date: str  # e.g. YYYYMMDD
    location: str
    is_aeon_holdout: bool

    class Config:
        strict = False   # allow extra (label/QC/feature) columns
        coerce = False   # wrong dtype raises instead of silently converting


def validate_master_table(df: pl.DataFrame) -> pl.DataFrame:
    return MasterTableSchema.validate(df)
```
Test `<series>/tests/test_validation.py`:
```python
import polars as pl
import pytest
from pandera.errors import SchemaError

from common.validation import validate_master_table


def _valid():
    return pl.DataFrame({
        "subject_id": ["s1"], "session_id": ["s1_20260101_A"],
        "year_month_date": ["20260101"], "location": ["A"], "is_aeon_holdout": [False]})


def test_valid_passes():
    assert validate_master_table(_valid()).height == 1


def test_extra_columns_allowed():
    assert "x" in validate_master_table(_valid().with_columns(pl.lit(1.0).alias("x"))).columns


def test_missing_required_column_raises():
    with pytest.raises(SchemaError):
        validate_master_table(_valid().drop("location"))


def test_wrong_type_raises():
    with pytest.raises(SchemaError):
        validate_master_table(_valid().with_columns(pl.col("is_aeon_holdout").cast(pl.Int64)))
```

---

## `<series>/common/tracking.py`
Portable: DB path derives from the series dir; git root via `git rev-parse`.
```python
"""MLflow logging entry point. Records split metadata + seed + git sha on every run.
Backend = SQLite under the series dir. Fail-fast: failures raise, no silent fallback."""
from __future__ import annotations

import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import mlflow

from common.splits import SplitSpec

_SERIES_DIR = Path(__file__).resolve().parent.parent   # common/ -> series dir
_DB = _SERIES_DIR / "mlflow.db"


def get_tracking_uri() -> str:
    return f"sqlite:///{_DB}"


def _repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=_SERIES_DIR, text=True).strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise RuntimeError(f"cannot locate git repo root: {exc}") from exc
    return Path(out)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"], cwd=_repo_root(), text=True).strip()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise RuntimeError(f"cannot resolve git sha: {exc}") from exc


@contextmanager
def start_run(exp_name: str, params: dict, tags: dict | None = None):
    mlflow.set_tracking_uri(get_tracking_uri())      # per-call: honors monkeypatched _DB in tests
    mlflow.set_experiment(exp_name)
    sha = _git_sha()
    with mlflow.start_run(run_name=f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{sha}") as run:
        mlflow.log_params(params)
        mlflow.set_tag("git_sha", sha)
        if tags:
            mlflow.set_tags(tags)
        yield run


def log_split_metadata(split: SplitSpec) -> None:
    mlflow.log_params({
        "split_strategy": split.strategy,
        "split_seed": split.seed,
        "n_train_subjects": len(split.train_subjects),
        "n_test_subjects": len(split.test_subjects),
        "aeon_locked": split.aeon_locked,
    })
    mlflow.set_tag("holdout_sites", ",".join(split.holdout_sites) if split.holdout_sites else "none")


def log_metrics(metrics: dict, step: int | None = None) -> None:
    mlflow.log_metrics(metrics, step=step)


def log_gate_results(gate_results: dict) -> None:
    mlflow.set_tags({f"gate_{k}": str(v) for k, v in gate_results.items()})


def log_artifact_dir(path) -> None:
    mlflow.log_artifacts(str(path))
```
Test `<series>/tests/test_tracking.py`:
```python
import mlflow
import pytest

from common import tracking
from common.splits import SplitSpec


@pytest.fixture()
def tmp_backend(tmp_path, monkeypatch):
    db = tmp_path / "mlflow.db"
    monkeypatch.setattr(tracking, "_DB", db)
    return f"sqlite:///{db}"


def test_get_tracking_uri_points_to_series_db():
    assert tracking.get_tracking_uri().startswith("sqlite:///")
    assert tracking.get_tracking_uri().endswith("mlflow.db")


def test_start_run_records_params_seed_and_git_sha(tmp_backend):
    split = SplitSpec(seed=42, strategy="subject", train_subjects=("s1", "s2"), test_subjects=("s3",))
    with tracking.start_run("exp/test", {"seed": 42}) as run:
        tracking.log_split_metadata(split)
        tracking.log_metrics({"m": 0.5})
        run_id = run.info.run_id
    data = mlflow.tracking.MlflowClient(tracking_uri=tmp_backend).get_run(run_id).data
    assert data.params["seed"] == "42"
    assert data.params["split_strategy"] == "subject"
    assert data.metrics["m"] == 0.5
    assert "git_sha" in data.tags
```

---

## `<series>/common/dvc_link.py`
```python
"""MLflow<->DVC loose coupling. Logs dvc.lock output hashes to the active MLflow run as tags.
Reproducibility itself rests on the git-tracked dvc.lock + tracking's git_sha; this is a convenience layer."""
from __future__ import annotations

from pathlib import Path

import mlflow
import yaml


def read_dvc_lock(exp_dir) -> dict:
    """Parse <exp_dir>/dvc.lock -> {stage: {out_path: hash_value}}.

    Missing lock -> {}. Corrupt lock -> yaml.YAMLError (never swallowed).
    NOTE: in dvc.lock v2 `hash` is the algo NAME (md5/sha256); the value is under a key
    named by the algo -> `out.get("md5") or out.get(out.get("hash",""), "")`.
    """
    lock = Path(exp_dir) / "dvc.lock"
    if not lock.exists():
        return {}
    data = yaml.safe_load(lock.read_text()) or {}
    result: dict = {}
    for stage_name, stage in (data.get("stages") or {}).items():
        outs = {}
        for out in stage.get("outs", []) or []:
            outs[out["path"]] = out.get("md5") or out.get(out.get("hash", ""), "")
        result[stage_name] = outs
    return result


def log_dvc_versions(exp_dir) -> None:
    """Tag the active MLflow run with dvc.lock output hashes. Missing lock -> dvc_tracked=false (opt-in)."""
    if not (Path(exp_dir) / "dvc.lock").exists():
        mlflow.set_tag("dvc_tracked", "false")
        return
    mlflow.set_tag("dvc_tracked", "true")
    for stage, outs in read_dvc_lock(exp_dir).items():
        for path, h in outs.items():
            mlflow.set_tag(f"dvc.{stage}.{path}", h)
```
Test `<series>/tests/test_dvc_link.py`:
```python
import mlflow
import pytest
import yaml

from common import dvc_link, tracking

_LOCK = {"schema": "2.0", "stages": {"build_master_table": {"cmd": "x",
    "outs": [{"path": "outputs/master_table.parquet", "hash": "md5", "md5": "abc123"}]}}}


@pytest.fixture()
def tmp_backend(tmp_path, monkeypatch):
    db = tmp_path / "mlflow.db"
    monkeypatch.setattr(tracking, "_DB", db)
    return f"sqlite:///{db}"


def test_read_dvc_lock_parses_outs(tmp_path):
    (tmp_path / "dvc.lock").write_text(yaml.safe_dump(_LOCK))
    assert dvc_link.read_dvc_lock(tmp_path) == {"build_master_table": {"outputs/master_table.parquet": "abc123"}}


def test_read_dvc_lock_missing_returns_empty(tmp_path):
    assert dvc_link.read_dvc_lock(tmp_path) == {}


def test_read_dvc_lock_handles_sha256(tmp_path):
    lock = {"schema": "2.0", "stages": {"s": {"cmd": "x",
        "outs": [{"path": "outputs/y.parquet", "hash": "sha256", "sha256": "def456"}]}}}
    (tmp_path / "dvc.lock").write_text(yaml.safe_dump(lock))
    assert dvc_link.read_dvc_lock(tmp_path) == {"s": {"outputs/y.parquet": "def456"}}


def test_read_dvc_lock_corrupt_raises(tmp_path):
    (tmp_path / "dvc.lock").write_text("{ not: valid: yaml: :")
    with pytest.raises(yaml.YAMLError):
        dvc_link.read_dvc_lock(tmp_path)


def test_log_dvc_versions_tags_active_run(tmp_path, tmp_backend):
    (tmp_path / "dvc.lock").write_text(yaml.safe_dump(_LOCK))
    with tracking.start_run("exp/dvc", {"seed": 1}) as run:
        dvc_link.log_dvc_versions(tmp_path)
        run_id = run.info.run_id
    tags = mlflow.tracking.MlflowClient(tracking_uri=tmp_backend).get_run(run_id).data.tags
    assert tags["dvc_tracked"] == "true"
    assert tags["dvc.build_master_table.outputs/master_table.parquet"] == "abc123"


def test_log_dvc_versions_no_lock_sets_false(tmp_path, tmp_backend):
    with tracking.start_run("exp/dvc2", {"seed": 1}) as run:
        dvc_link.log_dvc_versions(tmp_path)
        run_id = run.info.run_id
    tags = mlflow.tracking.MlflowClient(tracking_uri=tmp_backend).get_run(run_id).data.tags
    assert tags["dvc_tracked"] == "false"
```

---

## exp scaffold — `<series>/_template/`

`_template/conf/config.yaml`:
```yaml
exp_name: __EXP_NAME__
upstream:
  features: "<path to upstream feature parquet>"   # adapt
  labels_dir: "<path to labels>"                   # adapt
seed: 42
split:
  strategy: subject        # subject | site | aeon
  test_frac: 0.2
  holdout_sites: []
features: []
metrics: [icc, spearman_rho]
```

`_template/scripts/10_build_master_table.py` (note `parents[2]` = series dir):
```python
"""Build the 1-row-per-session master table, validate, split, leakage-check, log an MLflow run.
Real assembly is exp-specific (fill the TODO)."""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # series dir on sys.path

from common import tracking  # noqa: E402
from common.leakage_check import run_all_checks  # noqa: E402
from common.splits import make_subject_split  # noqa: E402
from common.validation import validate_master_table  # noqa: E402


def load_config() -> dict:
    return yaml.safe_load((Path(__file__).resolve().parents[1] / "conf" / "config.yaml").read_text())


def build_master_table(cfg: dict) -> pl.DataFrame:
    raise NotImplementedError("assemble features + labels into 1 row per session")  # TODO(exp)


def main() -> None:
    cfg = load_config()
    df = validate_master_table(build_master_table(cfg))
    split = make_subject_split(df, seed=cfg["seed"], test_frac=cfg["split"]["test_frac"])
    train = df.filter(pl.col("subject_id").is_in(list(split.train_subjects)))
    test = df.filter(pl.col("subject_id").is_in(list(split.test_subjects)))
    run_all_checks(train, test, split)
    with tracking.start_run(f"exp/{cfg['exp_name']}", {"seed": cfg["seed"]}):
        tracking.log_split_metadata(split)


if __name__ == "__main__":
    main()
```

`_template/scripts/20_build_x_vector.py`:
```python
"""Build derived feature/score vectors. Fill in for the exp."""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("build feature vectors")  # TODO(exp)


if __name__ == "__main__":
    main()
```

`_template/src/__init__.py`: empty. `_template/outputs/.gitkeep`: empty.

`_template/tests/test_smoke.py`:
```python
from pathlib import Path

import yaml


def test_template_config_parses_and_has_keys():
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "conf" / "config.yaml").read_text())
    for key in ("exp_name", "seed", "split", "upstream"):
        assert key in cfg
    assert cfg["split"]["strategy"] in {"subject", "site", "aeon"}


def test_template_dvc_yaml_parses_and_has_stages():
    spec = yaml.safe_load((Path(__file__).resolve().parents[1] / "dvc.yaml").read_text())
    assert "build_master_table" in spec["stages"]
    assert spec["stages"]["build_master_table"]["cmd"].startswith("uv run python scripts/10_")
```

`_template/dvc.yaml`:
```yaml
stages:
  build_master_table:
    cmd: uv run python scripts/10_build_master_table.py
    deps:
      - scripts/10_build_master_table.py
      - conf/config.yaml
    outs:
      - outputs/master_table.parquet
  build_x_vector:
    cmd: uv run python scripts/20_build_x_vector.py
    deps:
      - scripts/20_build_x_vector.py
      - outputs/master_table.parquet
    outs:
      - outputs/x_vector.parquet
```

`_template/README.md`: a stub with `# __EXP_NAME__`, the run commands (`uv run python .../scripts/10_...` and `uv run dvc repro`), and a "対応 Gate / hypothesis" placeholder.

---

## `<series>/scripts/new_exp.py`
```python
"""Clone _template/ into a new expNNN/, substituting __EXP_NAME__. Ensures outputs/ exists."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]   # series dir
_TEMPLATE = _ROOT / "_template"
_PLACEHOLDER = "__EXP_NAME__"


def create_exp(name: str, base_dir: Path | None = None, force: bool = False) -> Path:
    base_dir = base_dir or _ROOT
    dest = base_dir / name
    if dest.exists() and any(dest.iterdir()) and not force:
        raise FileExistsError(f"{dest} exists and is non-empty (use force=True)")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(_TEMPLATE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for path in dest.rglob("*"):
        if path.is_file() and path.suffix in {".yaml", ".md", ".py"}:
            text = path.read_text()
            if _PLACEHOLDER in text:
                path.write_text(text.replace(_PLACEHOLDER, name))
    (dest / "outputs").mkdir(exist_ok=True)   # robust: outputs/.gitkeep may be gitignored
    return dest


def main() -> None:
    p = argparse.ArgumentParser(description="Create a new exp from _template")
    p.add_argument("--name", required=True, help="e.g. exp001_master_table")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    print(f"created: {create_exp(args.name, force=args.force)}")


if __name__ == "__main__":
    main()
```
Test `<series>/tests/test_new_exp.py`:
```python
import importlib.util
from pathlib import Path

import pytest

_SPEC = Path(__file__).resolve().parents[1] / "scripts" / "new_exp.py"


def _load():
    spec = importlib.util.spec_from_file_location("new_exp", _SPEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_create_exp_copies_substitutes_and_makes_outputs(tmp_path):
    dest = _load().create_exp("exp999_smoke", base_dir=tmp_path)
    assert (dest / "conf" / "config.yaml").exists()
    assert (dest / "outputs").exists()
    assert "__EXP_NAME__" not in (dest / "conf" / "config.yaml").read_text()
    assert "exp999_smoke" in (dest / "conf" / "config.yaml").read_text()


def test_create_exp_refuses_existing_without_force(tmp_path):
    mod = _load()
    mod.create_exp("exp999_smoke", base_dir=tmp_path)
    with pytest.raises(FileExistsError):
        mod.create_exp("exp999_smoke", base_dir=tmp_path, force=False)
```

---

## SDD specs — `<series>/specs/` (pre-registration; adapt the content)

`specs/feature_availability.yaml` — machine-readable column policy:
```yaml
# source in {insole, label, context, derived}; leak_risk documents why a column must/most-not be a model input
columns:
  subject_id:      {available: true, leak_risk: "split key - never a feature", source: derived}
  location:        {available: true, leak_risk: "site holdout key - confound", source: context}
  is_aeon_holdout: {available: true, leak_risk: "holdout flag - never a feature", source: derived}
  # add your feature/label columns here, flagging any that must NOT be a model input
```

`specs/hypotheses.md`, `specs/metrics.md`, `specs/split_policy.md` — one page each: pre-register the hypotheses/gates (before running), the primary metrics + multiple-comparison correction, and the split policy (subject/site/holdout rules, seed). Keeping these BEFORE experiments run is the anti-p-hacking guardrail.

A `<series>/tests/test_specs.py` that asserts `feature_availability.yaml` parses with the `{available, leak_risk, source}` shape and the md docs are non-empty is a cheap safety net.

---

## ADR base — `docs/adr/` (repo root)

`docs/adr/README.md`: one decision per file; `NNNN-kebab-title.md`; Status `PROPOSED -> ACCEPTED -> SUPERSEDED by NNNN`.

`docs/adr/0000-template.md`:
```markdown
# ADR: <title>

**Status**: PROPOSED
**Date**: YYYY-MM-DD
**Scope**: <repo-wide | expNNN>

## Context
<background, constraints>

## Decision
<what was decided>

## Consequences
### Positive
-
### Negative
-
### Neutral
-

## Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
|  |  |

## References
-
```
Record the setup decisions themselves as `0001..` (e.g. "adopt MLflow SQLite backend", "adopt DVC data/pipeline versioning", "leakage-proof split policy") — dogfooding the ADR base is the fastest way to seed it.
