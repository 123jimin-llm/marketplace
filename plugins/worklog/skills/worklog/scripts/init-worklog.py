#!/usr/bin/env python3
"""Scaffold a worklog directory tree.

Usage:
    init-worklog.py [path]          # default: ./worklog
"""

import argparse
from pathlib import Path

DIRS = [
    "",
    "task",
    "plan",
    "spec",
    "tag",
    "archive",
    "archive/task",
    "archive/plan",
]


def init_worklog(root: Path) -> None:
    for rel in DIRS:
        d = root / rel if rel else root
        d.mkdir(parents=True, exist_ok=True)

        # Write .gitkeep for leaf directories that hold items
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists() and rel:  # skip root
            gitkeep.touch()
            print(f"  wrote {gitkeep}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a worklog directory tree.")
    parser.add_argument("path", nargs="?", default="./worklog", help="Root path for the worklog (default: ./worklog)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    print(f"Initializing worklog at {root}")
    init_worklog(root)
    print("Done.")


if __name__ == "__main__":
    main()
