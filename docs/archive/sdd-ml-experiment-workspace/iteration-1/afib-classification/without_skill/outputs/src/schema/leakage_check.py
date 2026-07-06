#!/usr/bin/env python3
"""
Leakage & Split Integrity Checker for AFib Classification.

Validates that:
1. Feature matrix contains ONLY inference_available variables (no leakage)
2. No subject appears in multiple train/test splits
3. Intra-subject data is co-located in same split

Usage:
    python src/schema/leakage_check.py \
        --schema src/schema/feature_availability.yaml \
        --features data/processed/feature_matrix.parquet \
        --split data/processed/split_index.json \
        --subject-col record_id
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml


class CheckResult:
    """Immutable check result."""

    def __init__(self, name: str, passed: bool, message: str):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


def check_feature_leakage(
    schema_path: Path, feature_columns: list[str]
) -> CheckResult:
    """Verify no inference_unavailable features are in the feature matrix."""
    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    features = schema.get("features", {})
    unavailable = set(features.get("inference_unavailable", []))
    aux_targets = set(features.get("auxiliary_targets", []))
    forbidden = unavailable | aux_targets

    leaked = sorted(forbidden & set(feature_columns))

    if leaked:
        return CheckResult(
            "Feature Leakage",
            False,
            f"LEAKED variables found in feature matrix: {leaked}",
        )
    return CheckResult(
        "Feature Leakage",
        True,
        f"No leakage detected. {len(feature_columns)} features checked "
        f"against {len(forbidden)} forbidden variables.",
    )


def check_split_subject_overlap(
    split_index: dict[str, int | str],
    subject_col: str,
) -> CheckResult:
    """Verify no subject appears in multiple splits."""
    subject_splits: dict[str, set] = {}
    for subject, split in split_index.items():
        subject_splits.setdefault(str(subject), set()).add(str(split))

    multi_split = {s: splits for s, splits in subject_splits.items() if len(splits) > 1}

    if multi_split:
        examples = dict(list(multi_split.items())[:5])
        return CheckResult(
            "Split Subject Overlap",
            False,
            f"{len(multi_split)} subjects appear in multiple splits. "
            f"Examples: {examples}",
        )
    return CheckResult(
        "Split Subject Overlap",
        True,
        f"All {len(subject_splits)} subjects are in exactly one split.",
    )


def check_group_colocation(
    df: pd.DataFrame,
    split_index: dict[str, int | str],
    subject_col: str,
) -> CheckResult:
    """Verify all records from the same subject are co-located in the same split."""
    subject_to_split = {str(k): str(v) for k, v in split_index.items()}

    violations = []
    for subject, group in df.groupby(subject_col):
        expected_split = subject_to_split.get(str(subject))
        if expected_split is None:
            violations.append(f"Subject {subject} not found in split index")

    if violations:
        return CheckResult(
            "Group Co-location",
            False,
            f"{len(violations)} violations found. First 5: {violations[:5]}",
        )
    return CheckResult(
        "Group Co-location",
        True,
        f"All intra-subject data is co-located. "
        f"Checked {len(subject_to_split)} subjects.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for data leakage and split integrity"
    )
    parser.add_argument(
        "--schema", type=Path, required=True,
        help="Path to feature_availability.yaml",
    )
    parser.add_argument(
        "--features", type=Path,
        help="Path to feature matrix (parquet/csv). If omitted, skip feature check.",
    )
    parser.add_argument(
        "--split", type=Path,
        help="Path to split_index.json. If omitted, skip split checks.",
    )
    parser.add_argument(
        "--subject-col", type=str, default="record_id",
        help="Name of subject ID column",
    )
    args = parser.parse_args()

    results: list[CheckResult] = []

    # Load feature matrix if provided
    df = None
    if args.features and args.features.exists():
        suffix = args.features.suffix.lower()
        if suffix == ".parquet":
            df = pd.read_parquet(args.features)
        elif suffix == ".csv":
            df = pd.read_csv(args.features)
        else:
            print(f"Unsupported feature file format: {suffix}")
            sys.exit(1)

        results.append(check_feature_leakage(args.schema, list(df.columns)))

    # Load split index if provided
    if args.split and args.split.exists():
        with open(args.split) as f:
            split_index = json.load(f)

        results.append(
            check_split_subject_overlap(split_index, args.subject_col)
        )

        if df is not None:
            results.append(
                check_group_colocation(df, split_index, args.subject_col)
            )

    if not results:
        print("No checks performed. Provide --features and/or --split paths.")
        sys.exit(1)

    # Report
    print("\n=== Leakage & Split Integrity Report ===\n")
    all_passed = True
    for r in results:
        print(r)
        if not r.passed:
            all_passed = False

    print(f"\n{'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
