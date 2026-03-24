"""Phase C: Holdout Evaluation -- ONE-SHOT protocol.

This script MUST be run at most once. Re-running on holdout
after seeing results constitutes p-hacking.

Gate: PR-AUC >= 0.65 on holdout

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

    # Report details
    logger.info("Holdout Details:")
    for detail_name, value in results.details.items():
        logger.info(f"  {detail_name}: {value}")

    if results.all_gates_passed:
        logger.info("Phase C: ALL GATES PASSED -- model validated on holdout")
    else:
        logger.warning(
            "Phase C: GATE FAILURE on holdout. "
            "Do NOT re-tune. Return to CV and document deviation."
        )

    # Always exit 0 for holdout -- the result is the result
    # Log pass/fail in experiment tracking for the record
    sys.exit(0)


if __name__ == "__main__":
    main()
