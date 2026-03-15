#!/usr/bin/env python3
"""Scaffold a worklog directory tree.

Usage:
    init-worklog.py [path]          # default: ./worklog
"""

import argparse
import shutil
from pathlib import Path

DIRS = [
    "",
    "task",
    "plan",
    "spec",
    "archive",
    "archive/task",
    "archive/plan",
    "archive/spec",
    "script",
]

# Scripts to copy into worklog/script/
SCRIPT_DIR = Path(__file__).resolve().parent


def init_worklog(root: Path) -> None:
    for rel in DIRS:
        d = root / rel if rel else root
        d.mkdir(parents=True, exist_ok=True)

        # Write .gitkeep for leaf directories that hold items
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists() and rel:  # skip root
            gitkeep.touch()
            print(f"  wrote {gitkeep}")

    # Create tags.md at worklog root if it doesn't exist
    tags_file = root / "tags.md"
    if not tags_file.exists():
        tags_file.write_text("# Tags\n", encoding="utf-8")
        print(f"  wrote {tags_file}")

    # Copy scripts and lib into worklog/script/
    _copy_scripts(root / "script")


def _copy_scripts(dest: Path) -> None:
    """Copy worklog scripts into dest, overwriting older copies."""
    dest.mkdir(parents=True, exist_ok=True)

    for src in SCRIPT_DIR.iterdir():
        if src.suffix == ".py" and src.name != "init-worklog.py":
            target = dest / src.name
            shutil.copy2(src, target)
            print(f"  copied {target}")


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
