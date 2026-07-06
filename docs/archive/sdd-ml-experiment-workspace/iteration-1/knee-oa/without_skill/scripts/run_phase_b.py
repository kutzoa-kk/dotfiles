"""Phase B runner -- cross-validation training and evaluation.

Trains LightGBM and XGBoost models with GroupKFold 5-fold CV.
Gate: pooled RMSE <= 1.0

Usage:
    python scripts/run_phase_b.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_access import load_merged_dataset
from src.features.feature_matrix_builder import build_feature_matrix
from src.models.ordinal_trainer import train_ordinal_model
from src.models.phase_b_evaluator import evaluate_phase_b
from src.schema.leakage_check import check_feature_leakage
from src.split_generator import generate_cv_split_index, save_split_index

OUTPUT_DIR = Path("outputs/phase_b")
SCHEMA_PATH = Path("src/schema/feature_availability.yaml")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Phase B: Cross-Validation Training ===\n")

    # 1. Load and build feature matrix
    print("Loading data and building feature matrix...")
    df = load_merged_dataset()
    fm, feature_cols = build_feature_matrix(df, SCHEMA_PATH)
    print(f"  Feature matrix: {fm.shape[0]} rows, {len(feature_cols)} features")

    # 2. Leakage check
    print("\nRunning leakage check...")
    leakage_result = check_feature_leakage(SCHEMA_PATH, feature_cols)
    print(f"  {leakage_result}")
    if not leakage_result.passed:
        print("FATAL: Feature leakage detected. Aborting.")
        sys.exit(1)

    # 3. Generate CV splits
    print("\nGenerating GroupKFold splits...")
    split_index = generate_cv_split_index(fm, n_splits=5, group_col="patient_id")
    save_split_index(split_index, OUTPUT_DIR / "cv_split_index.json")
    print(f"  {len(split_index)} patients assigned to 5 folds")

    # 4. Train models
    all_results = []
    for model_type in ["lightgbm", "xgboost"]:
        print(f"\nTraining {model_type}...")
        training_result = train_ordinal_model(
            feature_matrix=fm,
            split_index=split_index,
            feature_cols=feature_cols,
            target_col="kl_grade",
            group_col="patient_id",
            model_type=model_type,
            n_splits=5,
        )

        # Evaluate
        eval_report = evaluate_phase_b(training_result)
        print(f"  {eval_report.description}")

        all_results.append({
            "model_type": model_type,
            "metrics": eval_report.metrics,
            "gate_passed": eval_report.gate_passed,
            "description": eval_report.description,
            "feature_importance": dict(
                sorted(
                    training_result.feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:20]
            ),
        })

    # 5. Gate check (best model)
    any_passed = any(r["gate_passed"] for r in all_results)
    print(f"\n=== Phase B Gate: {'PASS' if any_passed else 'FAIL'} ===")

    # 6. Save results
    output_file = OUTPUT_DIR / "phase_b_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "results": all_results,
            "gate_passed": any_passed,
        }, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")

    if not any_passed:
        print("\nPhase B gate FAILED. Cannot proceed to Phase C.")
        sys.exit(1)
    else:
        best = min(all_results, key=lambda r: r["metrics"]["rmse"])
        print(f"\nPhase B gate PASSED. Best model: {best['model_type']} "
              f"(RMSE={best['metrics']['rmse']:.3f})")
        print("Proceed to Phase C (ONE-SHOT holdout).")


if __name__ == "__main__":
    main()
