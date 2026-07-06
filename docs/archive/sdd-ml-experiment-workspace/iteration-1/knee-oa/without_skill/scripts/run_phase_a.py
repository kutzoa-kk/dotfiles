"""Phase A runner -- biomarker correlation verification.

Tests:
    H1: Knee angle features correlate with KL grade (rho >= 0.4)
    H2: Gait cycle features correlate with KL grade (rho >= 0.4)

Gate: At least one of H1 or H2 must pass to proceed to Phase B.

Usage:
    python scripts/run_phase_a.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_access import load_merged_dataset
from src.models.phase_a_evaluator import check_gate_conditions, run_phase_a_evaluation
from src.schema.leakage_check import check_feature_leakage

OUTPUT_DIR = Path("outputs/phase_a")
SCHEMA_PATH = Path("src/schema/feature_availability.yaml")

# Feature lists (expand as needed when actual data is available)
KNEE_ANGLE_COLS = [
    "knee_flex_max", "knee_flex_min", "knee_rom",
    "knee_angle_at_heel_strike", "knee_angle_at_toe_off",
    "knee_flex_peak_swing", "knee_flex_peak_stance",
    "knee_angular_velocity_max", "knee_angular_velocity_min",
    "knee_angular_velocity_mean", "knee_angular_velocity_std",
    "knee_angle_cv", "knee_angle_std", "knee_angle_iqr",
]

GAIT_CYCLE_COLS = [
    "stance_phase_pct", "swing_phase_pct",
    "double_support_pct", "single_support_pct",
    "cadence", "stride_length", "gait_speed",
    "step_width", "step_length_asymmetry",
    "gait_cycle_duration", "gait_cycle_variability",
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Phase A: Biomarker Correlation Verification ===\n")

    # 1. Load data
    print("Loading data...")
    df = load_merged_dataset()
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # 2. Leakage check
    print("\nRunning leakage check...")
    leakage_result = check_feature_leakage(SCHEMA_PATH, list(df.columns))
    print(f"  {leakage_result}")

    # 3. Run Phase A evaluation
    print("\nRunning Phase A hypothesis tests...")
    reports = run_phase_a_evaluation(df, KNEE_ANGLE_COLS, GAIT_CYCLE_COLS)

    # 4. Report results
    print("\n=== Phase A Results ===\n")
    results = []
    for report in reports:
        print(f"  [{report.hypothesis}] {report.description}")
        results.append({
            "hypothesis": report.hypothesis,
            "metrics": report.metrics,
            "gate_passed": report.gate_passed,
            "description": report.description,
        })

    # 5. Gate check
    gate_passed = check_gate_conditions(reports)
    print(f"\n=== Phase A Gate: {'PASS' if gate_passed else 'FAIL'} ===")

    # 6. Save results
    output_file = OUTPUT_DIR / "phase_a_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "reports": results,
            "gate_passed": gate_passed,
        }, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")

    if not gate_passed:
        print("\nPhase A gate FAILED. Cannot proceed to Phase B.")
        sys.exit(1)
    else:
        print("\nPhase A gate PASSED. Proceed to Phase B.")


if __name__ == "__main__":
    main()
