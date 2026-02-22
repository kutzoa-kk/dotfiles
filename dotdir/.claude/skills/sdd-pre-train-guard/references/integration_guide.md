# Pre-Train Guard: Integration Guide

How to integrate `pre_train_guard.py` into your training pipeline so checks run automatically before every training run.

---

## 1. Hydra Callback Integration

Add a pre-training callback that runs the guard before model training begins.

### conf/callbacks/pre_train_guard.yaml

```yaml
pre_train_guard:
  _target_: src.callbacks.pre_train_guard.PreTrainGuardCallback
  project_dir: ${hydra:runtime.cwd}
  training_script: ${hydra:runtime.choices.model}
  subject_col: ${data.subject_col}
```

### src/callbacks/pre_train_guard.py

```python
"""Hydra callback that runs pre-train guard checks."""

import subprocess
import sys
from pathlib import Path

from omegaconf import DictConfig


class PreTrainGuardCallback:
    """Run pre-train guard checks before training."""

    def __init__(self, project_dir: str, training_script: str, subject_col: str):
        self.project_dir = Path(project_dir)
        self.training_script = training_script
        self.subject_col = subject_col

    def on_train_begin(self, cfg: DictConfig) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(self.project_dir / "src" / "schema" / "pre_train_guard.py"),
                "--project-dir", str(self.project_dir),
                "--training-script", self.training_script,
                "--subject-col", self.subject_col,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            raise RuntimeError(
                "Pre-train guard checks FAILED. Fix issues before training."
            )
```

---

## 2. pytest Integration

Run the guard as a pytest fixture or test so CI blocks on failures.

### tests/test_pre_train_guard.py

```python
"""Test pre-train guard checks pass before training."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_dir():
    """Return the project root directory."""
    return Path(__file__).parent.parent


def test_pre_train_guard(project_dir):
    """All pre-train guard checks must pass."""
    result = subprocess.run(
        [
            sys.executable,
            str(project_dir / "src" / "schema" / "pre_train_guard.py"),
            "--project-dir", str(project_dir),
            "--subject-col", "subject_id",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Pre-train guard failed:\n{result.stdout}\n{result.stderr}"
    )
```

### Run in CI

```yaml
# .github/workflows/ci.yaml
jobs:
  pre-train-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pyyaml
      - run: python src/schema/pre_train_guard.py --project-dir . --subject-col subject_id
```

---

## 3. Makefile / Script Integration

### Makefile

```makefile
.PHONY: guard train

guard:
	python src/schema/pre_train_guard.py \
		--project-dir . \
		--subject-col subject_id

train: guard
	python src/models/train.py
```

### Shell wrapper

```bash
#!/bin/bash
set -euo pipefail

echo "Running pre-train guard..."
python src/schema/pre_train_guard.py \
    --project-dir . \
    --training-script src/models/train.py \
    --subject-col subject_id

echo "Guard passed. Starting training..."
python src/models/train.py "$@"
```

---

## 4. Deployment to Target Project

After the skill generates the script, copy it to the target project:

```bash
# Copy guard script to project
cp scripts/pre_train_guard.py <project>/src/schema/pre_train_guard.py

# Verify it works
cd <project>
python src/schema/pre_train_guard.py --project-dir . --help
```

---

## 5. Custom Check Extension

To add project-specific checks, extend the `CHECKS` list in `pre_train_guard.py`:

```python
def check_custom_rule(project_dir: Path, args: argparse.Namespace) -> CheckResult:
    """Your custom check logic here."""
    # Return CheckResult(name, passed, message)
    ...

# Add to the checks list in main()
results.append(check_custom_rule(project_dir, args))
```

All custom checks follow the same `CheckResult` immutable pattern and contribute to the final exit code.
