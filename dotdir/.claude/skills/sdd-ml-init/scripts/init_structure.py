#!/usr/bin/env python3
"""
SDD ML Project Initializer - Creates a Specification-Driven Development directory structure.

Usage:
    python init_structure.py [project_dir]

If project_dir is omitted, uses the current directory.
Creates the full SDD directory tree with .gitkeep files for empty directories.
"""

import sys
from pathlib import Path

DIRS = [
    "docs/specs",
    "docs/experiments",
    "src/schema",
    "src/features",
    "src/models",
    "conf",
    "data/raw",
    "data/processed",
    "notebooks",
]


def create_structure(root: Path) -> None:
    root = root.resolve()
    if not root.exists():
        root.mkdir(parents=True)
        print(f"Created project root: {root}")

    for d in DIRS:
        dirpath = root / d
        dirpath.mkdir(parents=True, exist_ok=True)
        gitkeep = dirpath / ".gitkeep"
        if not any(dirpath.iterdir()):
            gitkeep.touch()
        print(f"  {d}/")

    print(f"\nDirectory structure created at {root}")


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    create_structure(target)


if __name__ == "__main__":
    main()
