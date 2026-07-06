"""Phase A: Biomarker Correlation Validation

Validates that KL grade correlates with known biomechanical biomarkers
(knee angle features, gait cycle parameters) before prediction modeling.

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
    logger.info("=== Phase A: Biomarker Correlation Validation ===")

    results = run_phase_a_evaluation(cfg)

    # Report results
    logger.info("Phase A Results:")
    for metric_name, value in results.metrics.items():
        status = "PASS" if results.gates.get(metric_name, False) else "---"
        logger.info(f"  [{status}] {metric_name}: {value:.4f}")

    # Report gate checks
    logger.info("Gate checks:")
    for gate_name, passed in results.gates.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"  [{status}] {gate_name}")

    if results.all_gates_passed:
        logger.info("Phase A: ALL GATES PASSED -- proceed to Phase B")
        sys.exit(0)
    else:
        logger.warning("Phase A: GATE FAILURE -- do not proceed to Phase B")
        logger.warning("Diagnose issues before re-running. Do NOT skip to Phase B.")
        sys.exit(1)


if __name__ == "__main__":
    main()
