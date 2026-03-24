"""Classification metrics for AF detection.

Centralized metric computation for binary classification.
All metrics used across phases are defined here.
"""

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float]:
    """Compute classification metrics for binary AF detection.

    Args:
        y_true: Ground truth binary labels.
        y_prob: Predicted probabilities for the positive class.
        threshold: Decision threshold for binary predictions.

    Returns:
        Dictionary of metric name -> value.
    """
    y_pred = (y_prob >= threshold).astype(int)

    metrics = {
        "pr_auc": average_precision_score(y_true, y_prob),
        "roc_auc": roc_auc_score(y_true, y_prob),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
    }

    return metrics


def aggregate_fold_metrics(
    fold_metrics_list: list[dict[str, float]],
) -> dict[str, float]:
    """Aggregate metrics across CV folds (mean and std).

    Args:
        fold_metrics_list: List of per-fold metric dictionaries.

    Returns:
        Dictionary with mean and std for each metric.
    """
    metric_names = fold_metrics_list[0].keys()
    aggregated: dict[str, float] = {}

    for name in metric_names:
        values = [m[name] for m in fold_metrics_list]
        aggregated[f"{name}_mean"] = float(np.mean(values))
        aggregated[f"{name}_std"] = float(np.std(values))

    return aggregated
