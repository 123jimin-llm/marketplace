#!/usr/bin/env python3
"""Get the next available ID for a worklog item class.

Usage:
    next-id.py task                 # -> t0001
    next-id.py plan -w ./worklog   # -> p0003
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
from frontmatter import scan_ids, CLASS_PREFIX


def main() -> None:
    parser = argparse.ArgumentParser(description="Get next available worklog ID.")
    parser.add_argument("item_class", choices=CLASS_PREFIX.keys(), help="Item class: task, plan, or spec")
    parser.add_argument("-w", "--worklog", default="./worklog", help="Worklog root directory (default: ./worklog)")
    args = parser.parse_args()

    root = Path(args.worklog).resolve()
    if not root.is_dir():
        print(f"Error: worklog directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    prefix = CLASS_PREFIX[args.item_class]
    ids = scan_ids(root, prefix)
    next_num = (max(ids) + 1) if ids else 1
    print(f"{prefix}{next_num:04d}")


if __name__ == "__main__":
    main()
