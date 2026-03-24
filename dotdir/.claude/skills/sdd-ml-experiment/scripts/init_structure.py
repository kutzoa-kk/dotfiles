#!/usr/bin/env python3
"""
SDD ML Experiment Initializer - Creates a phase-gated experiment directory structure.

Usage:
    python init_structure.py [experiment_dir]

If experiment_dir is omitted, uses the current directory.
Creates the full experiment directory tree with .gitkeep files for empty directories.
"""

import sys
from pathlib import Path

DIRS = [
    "conf",
    "conf/model",
    "conf/features",
    "conf/split",
    "src",
    "src/features",
    "src/models",
    "src/analysis",
    "src/schema",
    "scripts",
    "tests",
    "data/raw",
    "data/processed",
    "docs/specs",
    "docs/experiments",
    "notebooks",
]

INIT_FILES = [
    "src/__init__.py",
    "src/features/__init__.py",
    "src/models/__init__.py",
    "src/analysis/__init__.py",
    "src/schema/__init__.py",
]


def create_structure(root: Path) -> None:
    root = root.resolve()
    if not root.exists():
        root.mkdir(parents=True)
        print(f"Created experiment root: {root}")

    for d in DIRS:
        dirpath = root / d
        dirpath.mkdir(parents=True, exist_ok=True)
        gitkeep = dirpath / ".gitkeep"
        if not any(dirpath.iterdir()):
            gitkeep.touch()
        print(f"  {d}/")

    for f in INIT_FILES:
        filepath = root / f
        if not filepath.exists():
            filepath.touch()
            print(f"  {f}")

    print(f"\nExperiment structure created at {root}")


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    create_structure(target)


if __name__ == "__main__":
    main()
