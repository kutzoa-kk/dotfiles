# Metrics Specification -- Knee OA Progression

## Primary Metrics

| Metric | Phase | Gate Threshold | Description |
|--------|-------|----------------|-------------|
| Spearman rho (feature) | A | \|rho\| >= 0.4 | Feature-target correlation |
| RMSE | B | <= 1.0 | Root Mean Square Error on KL grade |
| RMSE | C | <= 1.0 | Holdout RMSE |
| Spearman rho (prediction) | C | >= 0.5 | Holdout prediction correlation |

## Secondary Metrics (reported, non-gating)

| Metric | Description |
|--------|-------------|
| MAE | Mean Absolute Error |
| Adjacent Accuracy | % predictions within +/- 1 KL grade |
| Exact Accuracy | % exact KL grade matches |
| Cohen's d | Effect size for known-group validity |
| AUROC | Area under ROC for group discrimination |
| Per-grade sensitivity | Sensitivity for each KL grade |
| Per-fold RMSE std | CV stability metric |
| Bootstrap 95% CI | Confidence intervals for primary metrics |

## Medical Compliance Requirements

1. **Confidence intervals**: All primary endpoints must include 95% bootstrap CI (n=1000).
2. **Calibration**: Predicted vs actual KL grade calibration plot required.
3. **Baseline comparison**: All models compared against mean predictor baseline.
4. **Per-grade breakdown**: Sensitivity and MAE reported for each KL grade.
5. **Clinical interpretability**: Top features must be clinically interpretable.

## Gate Decision Matrix

| Phase | Condition | Action if PASS | Action if FAIL |
|-------|-----------|----------------|----------------|
| A | H1 OR H2 rho >= 0.4 | Proceed to B | Stop; insufficient signal |
| B | RMSE <= 1.0 (any model) | Proceed to C | Stop; model insufficient |
| C | RMSE <= 1.0 AND rho >= 0.5 | Report success | Report failure; no iteration |
