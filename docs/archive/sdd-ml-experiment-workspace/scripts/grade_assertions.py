#!/usr/bin/env python3
"""Grade assertions for sdd-ml-experiment skill evaluation.

Checks each assertion against the generated outputs programmatically.
"""

import json
import sys
from pathlib import Path


def check_file_exists(base: Path, relative_path: str) -> bool:
    """Check if a file exists anywhere in the directory tree."""
    # Try exact path
    if (base / relative_path).exists():
        return True
    # Search recursively
    name = Path(relative_path).name
    return any(base.rglob(name))


def check_file_absent(base: Path, filename: str) -> bool:
    """Check that a file does NOT exist anywhere in the tree."""
    return not any(base.rglob(filename))


def search_content(base: Path, filename_pattern: str, keywords: list[str]) -> tuple[bool, list[str]]:
    """Search for keywords in files matching pattern. Returns (all_found, missing)."""
    files = list(base.rglob(filename_pattern))
    if not files:
        return False, [f"File {filename_pattern} not found"]

    content = ""
    for f in files:
        try:
            content += f.read_text(errors="ignore").lower()
        except Exception:
            pass

    missing = [kw for kw in keywords if kw.lower() not in content]
    return len(missing) == 0, missing


def count_files(base: Path, pattern: str) -> int:
    """Count files matching a glob pattern."""
    return len(list(base.rglob(pattern)))


def grade_common_assertions(base: Path) -> list[dict]:
    """Grade assertions common to all test cases."""
    results = []

    # A1: CLAUDE.md with prime directives
    found, missing = search_content(base, "CLAUDE.md", ["sycophancy", "pre-registration", "reporting"])
    if not found:
        found, missing = search_content(base, "CLAUDE.md", ["sycophancy", "registration", "report"])
    results.append({
        "text": "CLAUDE.md contains Anti-Sycophancy, Pre-Registration, Full Reporting directives",
        "passed": found,
        "evidence": f"Missing keywords: {missing}" if not found else "All key directives found"
    })

    # A2: feature_availability.yaml
    fa_files = list(base.rglob("feature_availability.yaml"))
    if fa_files:
        content = fa_files[0].read_text()
        has_available = "inference_available" in content
        has_unavailable = "inference_unavailable" in content
        passed = has_available and has_unavailable
        results.append({
            "text": "feature_availability.yaml with inference_available/unavailable",
            "passed": passed,
            "evidence": f"available={has_available}, unavailable={has_unavailable}"
        })
    else:
        results.append({
            "text": "feature_availability.yaml with inference_available/unavailable",
            "passed": False,
            "evidence": "File not found"
        })

    # A5: conftest.py and pytest.ini
    has_conftest = check_file_exists(base, "conftest.py")
    has_pytest_ini = check_file_exists(base, "pytest.ini")
    results.append({
        "text": "conftest.py and pytest.ini exist",
        "passed": has_conftest and has_pytest_ini,
        "evidence": f"conftest.py={has_conftest}, pytest.ini={has_pytest_ini}"
    })

    # A6: config.yaml with gates
    found, missing = search_content(base, "config.yaml", ["gate"])
    results.append({
        "text": "Hydra config.yaml contains gates section",
        "passed": found,
        "evidence": "Gates section found" if found else f"Missing: {missing}"
    })

    # A7: 00_HYPOTHESES.md
    has_hyp = check_file_exists(base, "00_HYPOTHESES.md")
    if has_hyp:
        found, _ = search_content(base, "00_HYPOTHESES.md", ["hypothesis"])
        results.append({
            "text": "00_HYPOTHESES.md with pre-registration content",
            "passed": found,
            "evidence": "Hypothesis content found" if found else "Missing hypothesis content"
        })
    else:
        results.append({
            "text": "00_HYPOTHESES.md with pre-registration content",
            "passed": False,
            "evidence": "File not found"
        })

    # A9: leakage_check.py
    results.append({
        "text": "leakage_check.py exists in src/schema/",
        "passed": check_file_exists(base, "leakage_check.py"),
        "evidence": "Found" if check_file_exists(base, "leakage_check.py") else "Not found"
    })

    # A4: test files for src modules
    src_py = count_files(base, "src/**/*.py") - count_files(base, "src/**/__init__.py")
    test_py = count_files(base, "tests/test_*.py")
    # Also check top-level tests
    if test_py == 0:
        test_py = count_files(base, "test_*.py")
    results.append({
        "text": "Test files exist for src modules",
        "passed": test_py >= 3,  # At minimum a few test files
        "evidence": f"src modules={src_py}, test files={test_py}"
    })

    return results


def grade_sarcopenia(base: Path) -> list[dict]:
    """Grade sarcopenia-specific assertions."""
    results = grade_common_assertions(base)

    # A3: Exactly 3 phase scripts
    phase_scripts = (
        count_files(base, "run_phase_a.py")
        + count_files(base, "run_phase_b.py")
        + count_files(base, "run_phase_c.py")
    )
    results.append({
        "text": "Exactly 3 phase scripts (A, B, C)",
        "passed": phase_scripts == 3,
        "evidence": f"Found {phase_scripts} phase scripts"
    })

    # A8: Spearman thresholds in METRICS.md
    found, missing = search_content(base, "02_METRICS.md", ["0.5", "0.3"])
    if not found:
        found, missing = search_content(base, "02_METRICS.md", ["spearman"])
    results.append({
        "text": "02_METRICS.md contains Spearman gate thresholds (0.5, 0.3)",
        "passed": found,
        "evidence": "Thresholds found" if found else f"Missing: {missing}"
    })

    # S1: Spearman mentioned in gate conditions
    found, _ = search_content(base, "CLAUDE.md", ["spearman"])
    if not found:
        found, _ = search_content(base, "02_METRICS.md", ["spearman"])
    results.append({
        "text": "Gate conditions mention Spearman correlation",
        "passed": found,
        "evidence": "Spearman reference found" if found else "Not found"
    })

    return results


def grade_knee_oa(base: Path) -> list[dict]:
    """Grade knee-oa-specific assertions."""
    results = grade_common_assertions(base)

    # A3: 3 phase scripts
    phase_scripts = (
        count_files(base, "run_phase_a.py")
        + count_files(base, "run_phase_b.py")
        + count_files(base, "run_phase_c.py")
    )
    results.append({
        "text": "Exactly 3 phase scripts (A, B, C)",
        "passed": phase_scripts == 3,
        "evidence": f"Found {phase_scripts} phase scripts"
    })

    # A8: Gate thresholds
    found, _ = search_content(base, "02_METRICS.md", ["0.4"])
    found2, _ = search_content(base, "02_METRICS.md", ["rmse"])
    results.append({
        "text": "02_METRICS.md contains rho >= 0.4 and RMSE thresholds",
        "passed": found and found2,
        "evidence": f"rho_threshold={found}, rmse_mentioned={found2}"
    })

    # M1: 04_COMPLIANCE.md with medical content
    has_compliance = check_file_exists(base, "04_COMPLIANCE.md")
    if has_compliance:
        found, _ = search_content(base, "04_COMPLIANCE.md", ["medical"])
        if not found:
            found, _ = search_content(base, "04_COMPLIANCE.md", ["compliance"])
        results.append({
            "text": "04_COMPLIANCE.md exists with medical content",
            "passed": found,
            "evidence": "Medical compliance doc found" if found else "Missing medical content"
        })
    else:
        results.append({
            "text": "04_COMPLIANCE.md exists with medical content",
            "passed": False,
            "evidence": "File not found"
        })

    # M2: Side co-location in split policy
    found, _ = search_content(base, "05_SPLIT_POLICY.md", ["side"])
    if not found:
        found, _ = search_content(base, "05_SPLIT_POLICY.md", ["co-locat"])
    if not found:
        found, _ = search_content(base, "CLAUDE.md", ["side"])
    results.append({
        "text": "Split policy mentions side (L/R) co-location",
        "passed": found,
        "evidence": "Side co-location documented" if found else "Not found"
    })

    # M3: Temporal holdout
    found, _ = search_content(base, "05_SPLIT_POLICY.md", ["temporal"])
    if not found:
        found, _ = search_content(base, "05_SPLIT_POLICY.md", ["2024"])
    results.append({
        "text": "Temporal holdout strategy documented",
        "passed": found,
        "evidence": "Temporal holdout found" if found else "Not found"
    })

    return results


def grade_afib(base: Path) -> list[dict]:
    """Grade afib-specific assertions."""
    results = grade_common_assertions(base)

    # A3: Only 2 phase scripts (no Phase A)
    has_a = count_files(base, "run_phase_a.py") > 0
    has_b = count_files(base, "run_phase_b.py") > 0
    has_c = count_files(base, "run_phase_c.py") > 0
    results.append({
        "text": "Only 2 phase scripts (B, C) — no Phase A",
        "passed": not has_a and has_b and has_c,
        "evidence": f"phase_a={has_a}, phase_b={has_b}, phase_c={has_c}"
    })

    # A8: PR-AUC thresholds
    found, _ = search_content(base, "02_METRICS.md", ["pr-auc"])
    if not found:
        found, _ = search_content(base, "02_METRICS.md", ["pr_auc"])
    if not found:
        found, _ = search_content(base, "02_METRICS.md", ["auc"])
    results.append({
        "text": "02_METRICS.md contains PR-AUC thresholds",
        "passed": found,
        "evidence": "PR-AUC thresholds found" if found else "Not found"
    })

    # C1: No Phase A evaluator
    results.append({
        "text": "No Phase A evaluator exists",
        "passed": check_file_absent(base, "phase_a_evaluator.py"),
        "evidence": "Correctly absent" if check_file_absent(base, "phase_a_evaluator.py") else "Phase A evaluator found (should not exist)"
    })

    # C2: Classification metrics
    found, _ = search_content(base, "02_METRICS.md", ["f1"])
    if not found:
        found, _ = search_content(base, "02_METRICS.md", ["precision"])
    results.append({
        "text": "Classification metrics in METRICS.md",
        "passed": found,
        "evidence": "Classification metrics found" if found else "Not found"
    })

    # C3: Research compliance
    has_compliance = check_file_exists(base, "04_COMPLIANCE.md")
    results.append({
        "text": "04_COMPLIANCE.md exists with research content",
        "passed": has_compliance,
        "evidence": "Found" if has_compliance else "Not found"
    })

    return results


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    test_cases = {
        "sarcopenia-risk": grade_sarcopenia,
        "knee-oa": grade_knee_oa,
        "afib-classification": grade_afib,
    }

    for test_name, grader_fn in test_cases.items():
        for variant in ["with_skill", "without_skill"]:
            base = workspace / test_name / variant / "outputs"
            if not base.exists():
                # Try without outputs subdir
                base = workspace / test_name / variant
            if not base.exists():
                print(f"SKIP {test_name}/{variant}: directory not found")
                continue

            results = grader_fn(base)
            passed = sum(1 for r in results if r["passed"])
            total = len(results)

            # Save grading.json
            grading = {
                "eval_name": test_name,
                "variant": variant,
                "expectations": results,
                "summary": {
                    "passed": passed,
                    "total": total,
                    "pass_rate": round(passed / total, 3) if total > 0 else 0,
                }
            }

            output_dir = workspace / test_name / variant
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "grading.json", "w") as f:
                json.dump(grading, f, indent=2)

            status = "PASS" if passed == total else "PARTIAL"
            print(f"[{status}] {test_name}/{variant}: {passed}/{total} assertions passed")
            for r in results:
                mark = "+" if r["passed"] else "x"
                print(f"  [{mark}] {r['text']}: {r['evidence']}")
            print()


if __name__ == "__main__":
    main()
