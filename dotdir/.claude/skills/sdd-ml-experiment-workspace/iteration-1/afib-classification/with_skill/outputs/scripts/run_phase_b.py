"""Phase B: Classification Model CV -- AF detection from ECG features.

Trains LightGBM / Logistic Regression with StratifiedGroupKFold 5-fold CV
and evaluates classification performance using PR-AUC.

Gate: PR-AUC >= 0.70 (mean across folds)

Usage:
    uv run python scripts/run_phase_b.py
    uv run python scripts/run_phase_b.py model=logistic_regression
"""

import logging
import sys

import hydra
from omegaconf import DictConfig

from src.models.phase_b_evaluator import run_phase_b_evaluation

logger = logging.getLogger(__name__)


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    logger.info("=== Phase B: Classification Model CV ===")
    logger.info(f"Model: {cfg.model.name}, Split: {cfg.split.name}")

    results = run_phase_b_evaluation(cfg)

    # Report per-fold results
    logger.info("Per-fold results:")
    for fold_result in results.fold_results:
        metrics_str = ", ".join(
            f"{k}={v:.4f}" for k, v in fold_result.metrics.items()
        )
        logger.info(f"  Fold {fold_result.fold_idx}: {metrics_str}")

    # Report aggregate results
    logger.info("Aggregate results:")
    for metric_name, value in results.aggregate_metrics.items():
        logger.info(f"  {metric_name}: {value:.4f}")

    # Report gate status
    logger.info("Gate conditions:")
    for gate_name, passed in results.gates.items():
        status = "PASS" if passed else "FAIL"
        threshold = getattr(cfg.gates.phase_b, gate_name, "N/A")
        actual = results.aggregate_metrics.get(f"{gate_name}_mean", "N/A")
        logger.info(f"  [{status}] {gate_name}: {actual} (threshold: {threshold})")

    if results.all_gates_passed:
        logger.info("Phase B: ALL GATES PASSED -- proceed to Phase C")
        sys.exit(0)
    else:
        logger.warning("Phase B: GATE FAILURE -- do not proceed to Phase C")
        logger.warning("Return to CV diagnostics. Do NOT evaluate on holdout.")
        sys.exit(1)


if __name__ == "__main__":
    main()
