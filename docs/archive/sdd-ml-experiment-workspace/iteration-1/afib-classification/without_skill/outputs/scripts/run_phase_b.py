"""Phase B: AF Classification from ECG Features (CV).

Entry point for the AFib Classification Phase B pipeline:
1. Load data (ECG features + clinical labels)
2. Build feature matrix (with leakage checks)
3. Load/generate split index
4. Train LightGBM + Logistic Regression (5-fold StratifiedGroupKFold CV)
5. Evaluate OOF predictions + gate check (PR-AUC >= 0.70)
6. Save results

Usage:
    cd outputs
    python scripts/run_phase_b.py
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

import polars as pl

# Add experiment root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_access import load_ecg_with_labels
from src.models.cv_trainer import train_cv_model
from src.models.phase_b_evaluator import evaluate_phase_b
from src.schema.leakage_check import check_feature_leakage
from src.split_generator import (
    generate_split_index,
    save_split_index,
    validate_split_integrity,
)

EXECUTION_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = EXECUTION_DIR / "data" / "processed"
SCHEMA_PATH = EXECUTION_DIR / "src" / "schema" / "feature_availability.yaml"

# Columns that are labels/metadata, not features
NON_FEATURE_COLS = {"record_id", "af_label", "diagnosis_date", "cardiologist_notes", "fold"}


def main() -> None:
    print("=" * 60)
    print("Phase B: AF Classification from ECG Features (CV)")
    print("=" * 60)

    # Step 1: Load data
    print("\n[1/6] Loading data...")
    dataset = load_ecg_with_labels()
    print(f"  Dataset: {dataset.shape[0]} rows, {dataset.shape[1]} cols")
    print(f"  Subjects: {len(dataset['record_id'].unique())}")

    af_counts = dataset.group_by("af_label").len().sort("af_label")
    print(f"  AF distribution: {af_counts.to_dicts()}")

    # Step 2: Identify feature columns
    print("\n[2/6] Identifying feature columns...")
    feature_cols = [
        c
        for c in dataset.columns
        if c not in NON_FEATURE_COLS and dataset.schema[c].is_numeric()
    ]
    print(f"  Feature columns: {len(feature_cols)}")

    # Leakage check
    print("\n  Running leakage check...")
    leakage_result = check_feature_leakage(SCHEMA_PATH, feature_cols)
    print(f"  {leakage_result}")
    if not leakage_result.passed:
        print("  ERROR: Leakage detected! Aborting.")
        sys.exit(1)

    # Step 3: Generate/load split index
    print("\n[3/6] Generating split index (5-fold StratifiedGroupKFold)...")
    split_index = generate_split_index(dataset, n_splits=5, seed=42)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    split_path = PROCESSED_DIR / "split_index.json"
    save_split_index(split_index, split_path)
    print(f"  Split index: {len(split_index)} subjects across {max(split_index.values()) + 1} folds")
    print(f"  Saved to {split_path}")

    # Validate split integrity
    violations = validate_split_integrity(dataset, split_index)
    if violations:
        print(f"  WARNING: Split integrity violations: {violations}")
    else:
        print("  Split integrity: OK")

    # Filter to subjects in split
    available_subjects = set(split_index.keys())
    dataset = dataset.filter(
        pl.col("record_id").cast(pl.Utf8).is_in(list(available_subjects))
    )

    # Step 4: Train models
    all_results = []
    for model_type in ["lightgbm", "logistic_regression"]:
        print(f"\n[4/6] Training {model_type} (5-fold CV)...")
        training_result = train_cv_model(
            feature_matrix=dataset,
            split_index=split_index,
            feature_cols=feature_cols,
            model_type=model_type,
            target_col="af_label",
            group_col="record_id",
        )

        for fr in training_result.fold_results:
            print(
                f"  Fold {fr.fold}: PR-AUC={fr.pr_auc:.4f}, "
                f"ROC-AUC={fr.roc_auc:.4f}, "
                f"n_train={fr.n_train} (pos={fr.n_positive_train}), "
                f"n_test={fr.n_test} (pos={fr.n_positive_test})"
            )
        print(f"\n  Pooled PR-AUC: {training_result.pooled_pr_auc:.4f}")
        print(f"  Pooled ROC-AUC: {training_result.pooled_roc_auc:.4f}")

        all_results.append(training_result)

    # Step 5: Evaluate
    print("\n[5/6] Evaluating Phase B predictions...")
    evaluations = []
    for training_result in all_results:
        report = evaluate_phase_b(training_result)
        evaluations.append(report)
        print(f"\n  {report.description}")
        for key, val in report.metrics.items():
            if isinstance(val, float):
                print(f"    {key}: {val:.4f}")

    # Step 6: Save results
    print("\n[6/6] Saving Phase B report...")
    best_eval = max(evaluations, key=lambda e: e.pr_auc)

    report_data = {
        "phase": "B",
        "n_samples": dataset.shape[0],
        "n_subjects": len(dataset["record_id"].unique()),
        "n_features": len(feature_cols),
        "gate_passed": best_eval.gate_passed,
        "best_model": best_eval.model_name,
        "models": [],
    }

    for eval_report, training_result in zip(evaluations, all_results):
        model_data = {
            "model_name": eval_report.model_name,
            "pr_auc": eval_report.pr_auc,
            "roc_auc": eval_report.roc_auc,
            "f1": eval_report.f1,
            "gate_passed": eval_report.gate_passed,
            "metrics": eval_report.metrics,
            "fold_results": [asdict(fr) for fr in training_result.fold_results],
        }
        report_data["models"].append(model_data)

    report_path = PROCESSED_DIR / "phase_b_report.json"
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Saved to {report_path}")

    # Save OOF predictions for best model
    best_result = all_results[evaluations.index(best_eval)]
    oof_path = PROCESSED_DIR / "phase_b_oof_predictions.parquet"
    best_result.oof_predictions.write_parquet(oof_path)
    print(f"  OOF predictions saved to {oof_path}")

    print("\n" + "=" * 60)
    print(f"Phase B complete. Best model: {best_eval.model_name}")
    print(f"Gate (PR-AUC >= 0.70): {'PASS' if best_eval.gate_passed else 'FAIL'}")
    print(f"PR-AUC: {best_eval.pr_auc:.4f}, ROC-AUC: {best_eval.roc_auc:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
