"""Phase C: Hold-out ONE-SHOT Evaluation.

Entry point for hold-out evaluation of AF classification:
1. Verify Phase B gate passed
2. Load data (ECG features + clinical labels)
3. Identify feature columns (with leakage check)
4. Generate hold-out split + save
5. Train hold-out model (train 80% -> 1 model)
6. Hold-out evaluation (ONE-SHOT, PR-AUC >= 0.65)
7. Save report (phase_c_report.json + holdout_predictions.parquet)

Usage:
    cd outputs
    python scripts/run_phase_c.py
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

import polars as pl

# Add experiment root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_access import load_ecg_with_labels
from src.models.holdout_trainer import train_holdout_model
from src.models.phase_c_evaluator import evaluate_holdout
from src.schema.leakage_check import check_feature_leakage
from src.split_generator import generate_holdout_split, save_split_index

EXECUTION_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = EXECUTION_DIR / "data" / "processed"
SCHEMA_PATH = EXECUTION_DIR / "src" / "schema" / "feature_availability.yaml"

# Columns that are labels/metadata, not features
NON_FEATURE_COLS = {"record_id", "af_label", "diagnosis_date", "cardiologist_notes", "fold"}


def main() -> None:
    print("=" * 60)
    print("Phase C: Hold-out ONE-SHOT Evaluation")
    print("=" * 60)

    # Step 1: Verify Phase B gate
    print("\n[1/7] Verifying Phase B gate...")
    phase_b_report_path = PROCESSED_DIR / "phase_b_report.json"
    if not phase_b_report_path.exists():
        print(f"  ERROR: Phase B report not found: {phase_b_report_path}")
        print("  Run Phase B first: python scripts/run_phase_b.py")
        sys.exit(1)

    with open(phase_b_report_path) as f:
        phase_b_report = json.load(f)

    if not phase_b_report.get("gate_passed"):
        print("  ERROR: Phase B gate FAILED. Cannot proceed to Phase C.")
        sys.exit(1)

    best_model = phase_b_report.get("best_model", "lightgbm")
    print(f"  Phase B gate: PASS (best model: {best_model})")

    # Extract optimal threshold from Phase B
    optimal_threshold = None
    for model_data in phase_b_report.get("models", []):
        if model_data["model_name"] == best_model:
            optimal_threshold = model_data["metrics"].get("optimal_threshold", 0.5)
            break

    # Step 2: Load data
    print("\n[2/7] Loading data...")
    dataset = load_ecg_with_labels()
    print(f"  Dataset: {dataset.shape[0]} rows, {dataset.shape[1]} cols")
    print(f"  Subjects: {len(dataset['record_id'].unique())}")

    # Step 3: Identify feature columns
    print("\n[3/7] Identifying feature columns...")
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

    # Step 4: Generate hold-out split
    print("\n[4/7] Generating hold-out split (seed=123, 80/20)...")
    holdout_split = generate_holdout_split(
        dataset,
        test_size=0.2,
        group_col="record_id",
        stratify_col="af_label",
        seed=123,
    )
    n_train_subjects = sum(1 for v in holdout_split.values() if v == 0)
    n_holdout_subjects = sum(1 for v in holdout_split.values() if v == 1)
    print(f"  Train subjects: {n_train_subjects}, Hold-out subjects: {n_holdout_subjects}")

    # Filter to subjects in split
    available_subjects = set(holdout_split.keys())
    dataset = dataset.filter(
        pl.col("record_id").cast(pl.Utf8).is_in(list(available_subjects))
    )

    # Save hold-out split
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    holdout_split_path = PROCESSED_DIR / "holdout_split.json"
    save_split_index(holdout_split, holdout_split_path)
    print(f"  Saved split to {holdout_split_path}")

    # Verify AF stratification
    for label, split_val in [("Train", 0), ("Hold-out", 1)]:
        subjects_in_set = [u for u, v in holdout_split.items() if v == split_val]
        subset = dataset.filter(pl.col("record_id").cast(pl.Utf8).is_in(subjects_in_set))
        af_counts = subset.group_by("af_label").len().sort("af_label")
        print(f"  {label} AF distribution: {af_counts.to_dicts()}")

    # Step 5: Train hold-out model
    print(f"\n[5/7] Training hold-out model ({best_model}, train 80% -> 1 model)...")
    holdout_result = train_holdout_model(
        feature_matrix=dataset,
        holdout_split=holdout_split,
        feature_cols=feature_cols,
        model_type=best_model,
        target_col="af_label",
        group_col="record_id",
    )
    print(f"  Train: {holdout_result.n_train_samples} samples, {holdout_result.n_train_subjects} subjects")
    print(f"  Hold-out: {holdout_result.n_holdout_samples} samples, {holdout_result.n_holdout_subjects} subjects")
    print(f"  Features: {holdout_result.n_features}")
    print(f"  Train positives: {holdout_result.n_positive_train}")
    print(f"  Hold-out positives: {holdout_result.n_positive_holdout}")

    # Step 6: ONE-SHOT evaluation
    print("\n[6/7] Hold-out ONE-SHOT evaluation (PR-AUC >= 0.65)...")
    evaluation = evaluate_holdout(holdout_result, optimal_threshold=optimal_threshold)
    print(f"\n  {evaluation.description}")
    print(f"    PR-AUC: {evaluation.pr_auc:.4f}")
    print(f"    ROC-AUC: {evaluation.roc_auc:.4f}")
    print(f"    F1: {evaluation.f1:.4f} (threshold={evaluation.optimal_threshold:.2f})")
    print(f"    Precision: {evaluation.precision:.4f}")
    print(f"    Recall: {evaluation.recall:.4f}")
    print(f"    Brier Score: {evaluation.brier_score:.4f}")
    print(f"    Baseline PR-AUC (prevalence): {evaluation.baseline_pr_auc:.4f}")
    print(f"    PR-AUC improvement: {evaluation.pr_auc_improvement:.4f}")

    # Step 7: Save report
    print("\n[7/7] Saving Phase C report...")
    report_data = {
        "phase": "C",
        "one_shot_execution_count": 1,
        "model_name": best_model,
        "n_samples_train": holdout_result.n_train_samples,
        "n_subjects_train": holdout_result.n_train_subjects,
        "n_samples_holdout": holdout_result.n_holdout_samples,
        "n_subjects_holdout": holdout_result.n_holdout_subjects,
        "n_features": holdout_result.n_features,
        "n_positive_train": holdout_result.n_positive_train,
        "n_positive_holdout": holdout_result.n_positive_holdout,
        "gate_passed": evaluation.gate_passed,
        "evaluation": asdict(evaluation),
    }
    report_data["evaluation"].pop("description", None)

    report_path = PROCESSED_DIR / "phase_c_report.json"
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Report saved to {report_path}")

    # Save holdout predictions
    pred_path = PROCESSED_DIR / "holdout_predictions.parquet"
    holdout_result.holdout_predictions.write_parquet(pred_path)
    print(f"  Predictions saved to {pred_path}")

    print("\n" + "=" * 60)
    gate_str = "PASS" if evaluation.gate_passed else "FAIL"
    print(f"Phase C complete. Gate (PR-AUC >= 0.65): {gate_str}")
    print(f"Hold-out PR-AUC: {evaluation.pr_auc:.4f}")
    print(f"ROC-AUC: {evaluation.roc_auc:.4f}")
    print(f"ONE-SHOT execution count: 1")
    print("=" * 60)


if __name__ == "__main__":
    main()
