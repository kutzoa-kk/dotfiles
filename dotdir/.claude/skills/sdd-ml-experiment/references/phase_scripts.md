# Phase Run Script Templates

Generate a `scripts/run_phase_X.py` for each defined phase. Each script follows this pattern.

## Common Structure

Every phase script:
1. Loads Hydra config
2. Sets up logging (MLflow or W&B)
3. Calls the phase evaluator
4. Checks gate conditions
5. Reports results with PASS/FAIL verdict
6. Returns exit code 0 (pass) or 1 (fail)

## Phase A Script Template (Validation)

```python
"""Phase A: {{phase_a_name}} — {{phase_a_description}}

Validates the target construct before any prediction modeling.

Usage:
    uv run python scripts/run_phase_a.py
    uv run python scripts/run_phase_a.py --config-name config
"""

import logging
import sys

import hydra
from omegaconf import DictConfig

from src.models.phase_a_evaluator import run_phase_a_evaluation

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    logger.info("=== Phase A: {{phase_a_name}} ===")

    results = run_phase_a_evaluation(cfg)

    # Report results
    logger.info("Phase A Results:")
    for metric_name, value in results.metrics.items():
        status = "PASS" if results.gates.get(metric_name, False) else "FAIL"
        logger.info(f"  [{status}] {metric_name}: {value:.4f}")

    if results.all_gates_passed:
        logger.info("Phase A: ALL GATES PASSED — proceed to Phase B")
        sys.exit(0)
    else:
        logger.warning("Phase A: GATE FAILURE — do not proceed to Phase B")
        logger.warning("Diagnose issues before re-running. Do NOT skip to Phase B.")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Phase B Script Template (Prediction)

```python
"""Phase B: {{phase_b_name}} — {{phase_b_description}}

Trains prediction model with cross-validation and evaluates performance.

Usage:
    uv run python scripts/run_phase_b.py
"""

import logging
import sys

import hydra
from omegaconf import DictConfig

from src.models.phase_b_evaluator import run_phase_b_evaluation

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    logger.info("=== Phase B: {{phase_b_name}} ===")

    results = run_phase_b_evaluation(cfg)

    # Report per-fold results
    logger.info("Per-fold results:")
    for fold_idx, fold_result in enumerate(results.fold_results):
        logger.info(f"  Fold {fold_idx}: {fold_result}")

    # Report aggregate results
    logger.info("Aggregate results:")
    for metric_name, value in results.aggregate_metrics.items():
        status = "PASS" if results.gates.get(metric_name, False) else "FAIL"
        logger.info(f"  [{status}] {metric_name}: {value:.4f}")

    if results.all_gates_passed:
        logger.info("Phase B: ALL GATES PASSED — proceed to Phase C")
        sys.exit(0)
    else:
        logger.warning("Phase B: GATE FAILURE — do not proceed to Phase C")
        logger.warning("Return to CV diagnostics. Do NOT evaluate on holdout.")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Phase C Script Template (Holdout)

```python
"""Phase C: Holdout Evaluation — ONE-SHOT protocol.

This script MUST be run at most once. Re-running on holdout
after seeing results constitutes p-hacking.

Usage:
    uv run python scripts/run_phase_c.py
"""

import logging
import sys

import hydra
from omegaconf import DictConfig

from src.models.phase_c_evaluator import run_phase_c_evaluation

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    logger.info("=== Phase C: Holdout Evaluation (ONE-SHOT) ===")
    logger.warning(
        "REMINDER: This is a one-shot evaluation. "
        "Do NOT re-tune and re-evaluate on holdout."
    )

    results = run_phase_c_evaluation(cfg)

    # Report results
    logger.info("Holdout Results:")
    for metric_name, value in results.metrics.items():
        status = "PASS" if results.gates.get(metric_name, False) else "FAIL"
        logger.info(f"  [{status}] {metric_name}: {value:.4f}")

    if results.all_gates_passed:
        logger.info("Phase C: ALL GATES PASSED — model validated on holdout")
    else:
        logger.warning(
            "Phase C: GATE FAILURE on holdout. "
            "Do NOT re-tune. Return to CV and document deviation."
        )

    # Always exit 0 for holdout — the result is the result
    # Log pass/fail in experiment tracking for the record
    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Custom Phase Script

For non-standard phases (e.g., "Phase B+: Extended analysis"), follow the same
pattern but adapt the evaluator call and gate conditions.

The key invariant: every script must report ALL metrics, not just passing ones.
