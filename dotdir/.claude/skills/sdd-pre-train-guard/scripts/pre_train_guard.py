#!/usr/bin/env python3
"""
Pre-Train Guard for SDD ML Projects.

Runs 5 checks before training to enforce SDD prime rules:
1. Feature Leakage (R3): No forbidden features in training data
2. Split Policy Consistency (R6): Code splitter matches documented policy
3. Preprocessing Inside Folds (R3, R4): No .fit() calls outside Pipeline
4. Validation Artifact (R4): validation_report.json exists and passes
5. Feature Schema Exists (R3, R4): feature_availability.yaml is valid

Usage:
    python pre_train_guard.py \\
        --project-dir /path/to/project \\
        --training-script src/models/train.py \\
        --subject-col subject_id
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Optional

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


# ---------------------------------------------------------------------------
# AST Visitors
# ---------------------------------------------------------------------------

KNOWN_PREPROCESSORS = frozenset({
    "StandardScaler", "MinMaxScaler", "RobustScaler",
    "LabelEncoder", "OrdinalEncoder", "OneHotEncoder",
    "SimpleImputer", "KNNImputer",
    "PCA", "TruncatedSVD",
    "PolynomialFeatures", "Normalizer",
    "MaxAbsScaler", "PowerTransformer", "QuantileTransformer",
})

PIPELINE_CLASSES = frozenset({
    "Pipeline", "make_pipeline", "ColumnTransformer",
})


class SplitterVisitor(ast.NodeVisitor):
    """Find sklearn splitter instantiations in source code."""

    KNOWN_SPLITTERS = frozenset({
        "KFold", "StratifiedKFold", "GroupKFold",
        "RepeatedKFold", "RepeatedStratifiedKFold",
        "ShuffleSplit", "StratifiedShuffleSplit", "GroupShuffleSplit",
        "LeaveOneOut", "LeaveOneGroupOut",
        "TimeSeriesSplit",
    })

    def __init__(self) -> None:
        self.found: list[dict[str, object]] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = self._get_call_name(node)
        if name and name in self.KNOWN_SPLITTERS:
            kwargs = {}
            for kw in node.keywords:
                if isinstance(kw.value, ast.Constant):
                    kwargs[kw.arg] = kw.value.value
            self.found.append({
                "class": name,
                "kwargs": kwargs,
                "lineno": node.lineno,
            })
        self.generic_visit(node)

    @staticmethod
    def _get_call_name(node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


class PreprocessorFitVisitor(ast.NodeVisitor):
    """Detect .fit()/.fit_transform() calls on known preprocessors outside Pipeline."""

    def __init__(self) -> None:
        self.violations: list[dict[str, object]] = []
        self._in_pipeline = False
        self._imported_names: dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.names:
            for alias in node.names:
                real_name = alias.name
                local_name = alias.asname or alias.name
                self._imported_names[local_name] = real_name
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for Pipeline/ColumnTransformer construction
        name = self._get_call_name(node)
        if name and name in PIPELINE_CLASSES:
            self._in_pipeline = True
            self.generic_visit(node)
            self._in_pipeline = False
            return

        # Check for .fit() or .fit_transform() on preprocessors
        if isinstance(node.func, ast.Attribute) and node.func.attr in (
            "fit", "fit_transform"
        ):
            obj_name = self._get_object_name(node.func.value)
            resolved = self._imported_names.get(obj_name, obj_name)
            if resolved in KNOWN_PREPROCESSORS and not self._in_pipeline:
                self.violations.append({
                    "preprocessor": resolved,
                    "method": node.func.attr,
                    "lineno": node.lineno,
                })
        self.generic_visit(node)

    @staticmethod
    def _get_call_name(node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    @staticmethod
    def _get_object_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            if isinstance(node.func, ast.Attribute):
                return node.func.attr
        return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_feature_schema(project_dir: Path) -> CheckResult:
    """Check 5: feature_availability.yaml exists and is valid."""
    schema_path = project_dir / "src" / "schema" / "feature_availability.yaml"

    if not schema_path.exists():
        return CheckResult(
            "Feature Schema",
            False,
            f"feature_availability.yaml not found at {schema_path}",
        )

    try:
        with open(schema_path) as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return CheckResult("Feature Schema", False, f"Invalid YAML: {e}")

    if not isinstance(schema, dict):
        return CheckResult("Feature Schema", False, "YAML root is not a mapping")

    features = schema.get("features", {})
    if not isinstance(features, dict):
        return CheckResult("Feature Schema", False, "Missing 'features' key")

    available = features.get("inference_available", [])
    if not available:
        return CheckResult(
            "Feature Schema",
            False,
            "inference_available list is empty or missing",
        )

    unavailable = features.get("inference_unavailable", [])
    return CheckResult(
        "Feature Schema",
        True,
        f"{len(available)} available, {len(unavailable)} unavailable features defined.",
    )


def check_feature_leakage(
    project_dir: Path,
    training_script: Optional[Path],
) -> CheckResult:
    """Check 1: No forbidden features leak into training."""
    schema_path = project_dir / "src" / "schema" / "feature_availability.yaml"

    if not schema_path.exists():
        return CheckResult(
            "Feature Leakage",
            False,
            "Cannot check: feature_availability.yaml not found",
        )

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    features = schema.get("features", {})
    unavailable = set(features.get("inference_unavailable", []))
    aux_targets = set(features.get("auxiliary_targets", []))
    forbidden = unavailable | aux_targets

    if not forbidden:
        return CheckResult(
            "Feature Leakage",
            True,
            "No forbidden features defined. Nothing to check.",
        )

    # Try to find feature columns referenced in training script
    if training_script and training_script.exists():
        source = training_script.read_text()
        # Heuristic: look for list literals or YAML references in the source
        # Extract quoted strings that might be column names
        quoted = set(re.findall(r'["\'](\w+)["\']', source))
        leaked = sorted(forbidden & quoted)
        if leaked:
            return CheckResult(
                "Feature Leakage",
                False,
                f"LEAKED variables found in {training_script.name}: {leaked}",
            )
        return CheckResult(
            "Feature Leakage",
            True,
            f"No leakage detected. Checked {len(quoted)} string literals "
            f"against {len(forbidden)} forbidden variables.",
        )

    # Fallback: check feature matrix if it exists
    feature_matrix = project_dir / "data" / "processed" / "feature_matrix.parquet"
    if feature_matrix.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(feature_matrix)
            leaked = sorted(forbidden & set(df.columns))
            if leaked:
                return CheckResult(
                    "Feature Leakage",
                    False,
                    f"LEAKED variables found in feature_matrix: {leaked}",
                )
            return CheckResult(
                "Feature Leakage",
                True,
                f"No leakage. {len(df.columns)} columns checked "
                f"against {len(forbidden)} forbidden.",
            )
        except ImportError:
            pass

    return CheckResult(
        "Feature Leakage",
        True,
        "No training script or feature matrix found. Schema-only check passed.",
    )


def check_split_policy(
    project_dir: Path,
    training_script: Optional[Path],
) -> CheckResult:
    """Check 2: CV splitter in code matches documented split policy."""
    spec_path = project_dir / "docs" / "specs" / "05_SPLIT_POLICY.md"

    if not spec_path.exists():
        return CheckResult(
            "Split Policy Consistency",
            False,
            "05_SPLIT_POLICY.md not found. Cannot verify split policy.",
        )

    spec_text = spec_path.read_text()

    # Extract CV strategy from spec
    spec_splitter = None
    spec_folds = None
    for line in spec_text.splitlines():
        lower = line.lower()
        # Look for splitter class names
        for name in SplitterVisitor.KNOWN_SPLITTERS:
            if name.lower() in lower:
                spec_splitter = name
                break
        # Look for fold count
        fold_match = re.search(r'(\d+)\s*-?\s*fold', lower)
        if fold_match:
            spec_folds = int(fold_match.group(1))

    if not spec_splitter:
        return CheckResult(
            "Split Policy Consistency",
            True,
            "No recognizable splitter found in spec. Skipping code comparison.",
        )

    # Parse training script for actual splitter usage
    if not training_script or not training_script.exists():
        return CheckResult(
            "Split Policy Consistency",
            True,
            f"Spec declares {spec_splitter} but no training script to verify against.",
        )

    source = training_script.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return CheckResult(
            "Split Policy Consistency",
            False,
            f"Cannot parse {training_script.name}: {e}",
        )

    visitor = SplitterVisitor()
    visitor.visit(tree)

    if not visitor.found:
        return CheckResult(
            "Split Policy Consistency",
            True,
            f"Spec declares {spec_splitter} but no splitter found in code. "
            "Manual verification recommended.",
        )

    for found in visitor.found:
        code_class = found["class"]
        code_folds = found["kwargs"].get("n_splits")
        if code_class != spec_splitter:
            return CheckResult(
                "Split Policy Consistency",
                False,
                f"Expected {spec_splitter} but found {code_class} "
                f"at line {found['lineno']}",
            )
        if spec_folds and code_folds and int(code_folds) != spec_folds:
            return CheckResult(
                "Split Policy Consistency",
                False,
                f"Expected {spec_folds}-fold but found n_splits={code_folds} "
                f"at line {found['lineno']}",
            )

    return CheckResult(
        "Split Policy Consistency",
        True,
        f"Code uses {spec_splitter} matching spec. "
        f"{len(visitor.found)} splitter instance(s) checked.",
    )


def check_preprocessing_in_folds(
    training_script: Optional[Path],
) -> CheckResult:
    """Check 3: No .fit() on preprocessors outside Pipeline context."""
    if not training_script or not training_script.exists():
        return CheckResult(
            "Preprocessing Inside Folds",
            True,
            "No training script provided. Skipping.",
        )

    source = training_script.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return CheckResult(
            "Preprocessing Inside Folds",
            False,
            f"Cannot parse {training_script.name}: {e}",
        )

    visitor = PreprocessorFitVisitor()
    visitor.visit(tree)

    if visitor.violations:
        details = "; ".join(
            f"{v['preprocessor']}.{v['method']}() at line {v['lineno']}"
            for v in visitor.violations
        )
        return CheckResult(
            "Preprocessing Inside Folds",
            False,
            f"{len(visitor.violations)} violation(s): {details}",
        )

    return CheckResult(
        "Preprocessing Inside Folds",
        True,
        "No unguarded .fit() calls found on known preprocessors.",
    )


def check_validation_artifact(project_dir: Path) -> CheckResult:
    """Check 4: validation_report.json exists and all checks passed."""
    report_path = project_dir / "data" / "processed" / "validation_report.json"

    if not report_path.exists():
        return CheckResult(
            "Validation Artifact",
            False,
            f"validation_report.json not found at {report_path}",
        )

    try:
        with open(report_path) as f:
            report = json.load(f)
    except json.JSONDecodeError as e:
        return CheckResult("Validation Artifact", False, f"Invalid JSON: {e}")

    required_keys = {"timestamp", "schema_version", "checks"}
    missing = required_keys - set(report.keys())
    if missing:
        return CheckResult(
            "Validation Artifact",
            False,
            f"Missing required keys: {sorted(missing)}",
        )

    checks = report.get("checks", [])
    if not checks:
        return CheckResult(
            "Validation Artifact",
            False,
            "No checks found in validation_report.json",
        )

    failed = [c for c in checks if not c.get("passed", False)]
    if failed:
        return CheckResult(
            "Validation Artifact",
            False,
            f"{len(failed)} of {len(checks)} checks failed in validation_report.json",
        )

    return CheckResult(
        "Validation Artifact",
        True,
        f"All {len(checks)} checks passed. "
        f"Report timestamp: {report.get('timestamp', 'unknown')}",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-Train Guard: 5 checks before training begins"
    )
    parser.add_argument(
        "--project-dir", type=Path, required=True,
        help="Root directory of the SDD ML project",
    )
    parser.add_argument(
        "--training-script", type=Path, default=None,
        help="Path to the training script (for AST analysis)",
    )
    parser.add_argument(
        "--subject-col", type=str, default="subject_id",
        help="Name of subject ID column",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    training_script = args.training_script
    if training_script:
        training_script = training_script.resolve()

    results: list[CheckResult] = [
        check_feature_schema(project_dir),
        check_feature_leakage(project_dir, training_script),
        check_split_policy(project_dir, training_script),
        check_preprocessing_in_folds(training_script),
        check_validation_artifact(project_dir),
    ]

    # Report
    print("\n=== Pre-Train Guard Report ===\n")
    all_passed = True
    for r in results:
        print(r)
        if not r.passed:
            all_passed = False

    print(f"\n{'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
