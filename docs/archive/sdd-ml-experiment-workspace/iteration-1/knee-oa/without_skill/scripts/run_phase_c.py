"""Phase C runner -- hold-out ONE-SHOT evaluation.

Trains on temporal train set (< 2024) and evaluates on holdout (>= 2024).
Gate: RMSE <= 1.0 AND Spearman rho >= 0.5

ONE-SHOT: This evaluation MUST NOT be iterated on. Run once, report results.

Usage:
    python scripts/run_phase_c.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_access import load_merged_dataset
from src.features.feature_matrix_builder import build_feature_matrix
from src.models.holdout_trainer import train_holdout_model
from src.models.phase_c_evaluator import evaluate_holdout
from src.schema.leakage_check import check_feature_leakage, check_temporal_holdout_integrity
from src.split_generator import generate_temporal_holdout_split, save_split_index

OUTPUT_DIR = Path("outputs/phase_c")
SCHEMA_PATH = Path("src/schema/feature_availability.yaml")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Phase C: Hold-Out ONE-SHOT Evaluation ===\n")
    print("WARNING: This is a ONE-SHOT evaluation. Do NOT iterate.\n")

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

    # 3. Temporal holdout split
    print("\nGenerating temporal holdout split (cutoff: 2024)...")
    holdout_split = generate_temporal_holdout_split(
        fm, group_col="patient_id", date_col="visit_date", cutoff_year=2024
    )
    save_split_index(holdout_split, OUTPUT_DIR / "holdout_split_index.json")
    n_train = sum(1 for v in holdout_split.values() if v == 0)
    n_test = sum(1 for v in holdout_split.values() if v == 1)
    print(f"  Train: {n_train} patients (< 2024), Holdout: {n_test} patients (>= 2024)")

    # 4. Temporal integrity check
    import pandas as pd
    fm_pd = fm.to_pandas()
    temporal_check = check_temporal_holdout_integrity(fm_pd, "patient_id")
    print(f"  {temporal_check}")

    # 5. Train and evaluate (ONE-SHOT)
    all_results = []
    for model_type in ["lightgbm", "xgboost"]:
        print(f"\nTraining {model_type} (holdout)...")
        holdout_result = train_holdout_model(
            feature_matrix=fm,
            holdout_split=holdout_split,
            feature_cols=feature_cols,
            target_col="kl_grade",
            group_col="patient_id",
            model_type=model_type,
        )

        # Evaluate
        evaluation = evaluate_holdout(holdout_result)
        print(f"  {evaluation.description}")

        all_results.append({
            "model_type": model_type,
            "rmse": evaluation.rmse,
            "mae": evaluation.mae,
            "spearman_rho": evaluation.spearman_rho,
            "adjacent_accuracy": evaluation.adjacent_accuracy,
            "exact_accuracy": evaluation.exact_accuracy,
            "baseline_rmse": evaluation.baseline_rmse,
            "rmse_improvement": evaluation.rmse_improvement,
            "ci_rmse": [evaluation.ci_rmse_lower, evaluation.ci_rmse_upper],
            "ci_rho": [evaluation.ci_rho_lower, evaluation.ci_rho_upper],
            "n_samples": evaluation.n_samples,
            "n_patients": evaluation.n_patients,
            "gate_rmse_passed": evaluation.gate_rmse_passed,
            "gate_rho_passed": evaluation.gate_rho_passed,
            "gate_passed": evaluation.gate_passed,
            "description": evaluation.description,
        })

    # 6. Final gate
    any_passed = any(r["gate_passed"] for r in all_results)
    print(f"\n=== Phase C Gate: {'PASS' if any_passed else 'FAIL'} ===")

    # 7. Save results
    output_file = OUTPUT_DIR / "phase_c_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "results": all_results,
            "gate_passed": any_passed,
            "one_shot_warning": "This evaluation is ONE-SHOT. Results must not be iterated upon.",
        }, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")

    if any_passed:
        best = min(all_results, key=lambda r: r["rmse"])
        print(f"\nBest model: {best['model_type']} "
              f"(RMSE={best['rmse']:.3f}, rho={best['spearman_rho']:.3f})")
    else:
        print("\nNo model passed the Phase C gate.")


if __name__ == "__main__":
    main()
