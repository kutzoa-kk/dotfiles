"""Phase A evaluator: Score Validation.

Validates the sarcopenia risk score construct before any prediction modeling.

Validations:
- Correlation between constructed score and known clinical indicators (e.g., SMI)
- Distribution sanity checks (no extreme skew, adequate variance)
- Batch effect checks across data collection conditions
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import polars as pl
from omegaconf import DictConfig
from scipy import stats

from src.data_access import load_data
from src.schema.leakage_check import check_feature_leakage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseAResult:
    """Immutable result container for Phase A evaluation."""

    metrics: dict[str, float]
    gates: dict[str, bool]
    details: dict = field(default_factory=dict)

    @property
    def all_gates_passed(self) -> bool:
        return all(self.gates.values())


def run_phase_a_evaluation(cfg: DictConfig) -> PhaseAResult:
    """Run Phase A validation checks.

    Validates the sarcopenia risk score construct by checking:
    1. Correlation with expected clinical correlates
    2. Score distribution properties
    3. Absence of batch effects

    Args:
        cfg: Hydra config with data paths, thresholds, etc.

    Returns:
        PhaseAResult with metrics and gate pass/fail status.
    """
    # 1. Load data
    df = load_data(cfg)
    logger.info(f"Phase A: loaded {len(df)} samples")

    # 2. Run leakage check
    check_feature_leakage(cfg)

    # 3. Compute sarcopenia risk score
    # TODO: Implement score construction logic
    # The score should be derived from clinical measurements
    target_col = cfg.data.target_column
    target_values = df.get_column(target_col).to_numpy()

    # 4. Validate construct
    metrics: dict[str, float] = {}
    gates: dict[str, bool] = {}
    details: dict = {}

    # Validation 1: Correlation with expected correlate
    # TODO: Replace with actual clinical correlate column
    # rho, p_value = stats.spearmanr(target_values, correlate_values)
    # metrics["spearman_rho"] = rho
    # metrics["spearman_p_value"] = p_value
    # gates["spearman_rho"] = rho >= cfg.gates.phase_a.min_spearman_rho

    # Validation 2: Score distribution
    metrics["target_mean"] = float(np.mean(target_values))
    metrics["target_std"] = float(np.std(target_values))
    metrics["target_skew"] = float(stats.skew(target_values))
    metrics["n_samples"] = float(len(target_values))

    # Gate: adequate variance (std > 0)
    gates["adequate_variance"] = float(np.std(target_values)) > 0.0

    logger.info(f"Phase A metrics: {metrics}")
    logger.info(f"Phase A gates: {gates}")

    return PhaseAResult(metrics=metrics, gates=gates, details=details)
