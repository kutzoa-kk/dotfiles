# Metrics -- afib-classification

## Primary Metric

### PR-AUC (Precision-Recall Area Under Curve)

**Rationale**: AF detection is typically a class-imbalanced problem. PR-AUC is more informative than ROC-AUC in imbalanced settings because it focuses on the performance of the positive (AF) class. A model that achieves high PR-AUC reliably identifies AF cases without excessive false positives.

**Computation**: `sklearn.metrics.average_precision_score(y_true, y_prob)`

## Secondary Metrics

| Metric | Description | Purpose |
|--------|-------------|---------|
| ROC-AUC | Area under ROC curve | Overall discriminative ability |
| F1 Score | Harmonic mean of precision and recall | Balanced classification quality |
| Precision | True positives / predicted positives | False positive control |
| Recall | True positives / actual positives | Sensitivity to AF detection |

## Phase Gates

### Phase B: Classification Model CV

| Gate | Metric | Operator | Threshold | Aggregation |
|------|--------|----------|-----------|-------------|
| B1 | PR-AUC | >= | 0.70 | Mean across 5 CV folds |

**On pass**: Proceed to Phase C holdout evaluation.
**On fail**: Return to feature engineering and model diagnostics. Investigate:
- Feature quality and informativeness
- Class imbalance handling
- Model hyperparameters
- Data quality issues

### Phase C: Holdout Evaluation

| Gate | Metric | Operator | Threshold | Evaluation |
|------|--------|----------|-----------|------------|
| C1 | PR-AUC | >= | 0.65 | Single holdout evaluation |

**On pass**: Model validated -- report results.
**On fail**: Do NOT re-tune on holdout. Document deviation from CV performance and investigate causes (distribution shift, overfitting, etc.).

## Reporting Requirements

All experiment reports must include:
1. Per-fold metrics table (all 5 folds)
2. Mean and standard deviation across folds
3. Confusion matrix at optimal threshold
4. PR curve and ROC curve visualizations
5. Feature importance ranking
6. Comparison across model types (LightGBM vs Logistic Regression)
