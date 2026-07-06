"""Phase B: Prediction Model CV — LightGBM with GroupKFold 5-fold.

Trains prediction model with cross-validation and evaluates performance.
Gate condition: Spearman rho >= 0.3

Usage:
    uv run python scripts/run_phase_b.py
    uv run python scripts/run_phase_b.py model=tuned_lgb
"""

import logging
import sys

import hydra
from omegaconf import DictConfig

from src.models.phase_b_evaluator import run_phase_b_evaluation

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    logger.info("=== Phase B: Prediction Model CV ===")

    results = run_phase_b_evaluation(cfg)

    # Report per-fold results
    logger.info("Per-fold results:")
    for fold_result in results.fold_results:
        logger.info(f"  Fold {fold_result.fold_idx}: {fold_result.metrics}")

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
