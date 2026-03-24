# Hypotheses -- afib-classification

## Pre-registered Hypotheses

### H1: ECG Feature-based AF Classification

**Statement**: ECG-derived features (RR interval statistics, P-wave morphology, QRS complex features, and heart rate variability metrics) can classify atrial fibrillation with clinically meaningful accuracy.

**Justification**: AF is characterized by irregular RR intervals, absent or irregular P-waves, and altered heart rate variability patterns. These physiological markers should be detectable through extracted ECG features.

**Primary metric**: PR-AUC (Precision-Recall Area Under Curve) -- chosen because AF detection is typically a class-imbalanced problem where positive class (AF) detection is the priority.

**Phase B gate**: PR-AUC >= 0.70 (CV mean)
**Phase C gate**: PR-AUC >= 0.65 (holdout)

### H2: RR Interval Irregularity as Primary Discriminator

**Statement**: RR interval variability features (rr_std, rr_iqr, rr_rmssd, rr_pnn50) will be among the top-ranked features by importance for AF classification.

**Justification**: The hallmark of AF is irregularly irregular RR intervals. These features should capture the core pathophysiology.

**Evaluation**: Feature importance ranking from LightGBM and logistic regression coefficients.

## Analysis Plan

1. Train LightGBM and Logistic Regression classifiers
2. Evaluate via StratifiedGroupKFold 5-fold CV (grouped by record_id)
3. Feature selection by domain knowledge (ECG morphology and rhythm features)
4. Compare model performance across feature groups (ablation study)
5. One-shot holdout evaluation for final validation

## Post-hoc Findings

_Any findings discovered after pre-registration must be documented below and labeled as exploratory._

(none yet)
