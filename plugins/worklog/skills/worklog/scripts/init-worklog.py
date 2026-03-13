#!/usr/bin/env python3
"""Scaffold a worklog directory tree with AGENTS.md files.

Usage:
    init-worklog.py [path]          # default: ./worklog
    init-worklog.py --force         # overwrite existing AGENTS.md files
"""

import argparse
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
REFERENCES = PLUGIN_ROOT / "references"

# (relative_path, reference_file_stem_or_None)
# None = leaf directory, gets .gitkeep only
TREE: list[tuple[str, str | None]] = [
    ("", "root"),
    ("task", "task"),
    ("plan", "plan"),
    ("spec", "spec"),
    ("tag", "tag"),
    ("script", "script"),
    ("archive", "archive"),
    ("archive/task", None),
    ("archive/plan", None),
]


def init_worklog(root: Path, force: bool = False) -> None:
    for rel, ref_stem in TREE:
        d = root / rel if rel else root
        d.mkdir(parents=True, exist_ok=True)

        # Write AGENTS.md from reference file
        if ref_stem is not None:
            agents_path = d / "AGENTS.md"
            if force or not agents_path.exists():
                content = (REFERENCES / f"{ref_stem}.md").read_text(encoding="utf-8")
                agents_path.write_text(content, encoding="utf-8")
                print(f"  wrote {agents_path}")
            else:
                print(f"  skip  {agents_path} (exists)")

        # Write .gitkeep for leaf directories that hold items
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists() and rel:  # skip root
            gitkeep.touch()
            print(f"  wrote {gitkeep}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a worklog directory tree.")
    parser.add_argument("path", nargs="?", default="./worklog", help="Root path for the worklog (default: ./worklog)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing AGENTS.md files")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    print(f"Initializing worklog at {root}")
    init_worklog(root, force=args.force)
    print("Done.")


if __name__ == "__main__":
    main()
