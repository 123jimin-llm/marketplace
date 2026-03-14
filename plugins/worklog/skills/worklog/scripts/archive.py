#!/usr/bin/env python3
"""Move completed task/plan folders to the archive.

Usage:
    archive.py t0001                # archive task t0001
    archive.py p0003 --force        # skip status check
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
from frontmatter import parse_item

ID_RE = re.compile(r"^([tp])(\d{4})$")

CLASS_MAP = {"t": "task", "p": "plan"}
DONE_STATUS = {"t": "done", "p": ("abandoned", "active")}  # plans archive when fully applied or abandoned


def find_item(worklog_root: Path, prefix: str, item_id: str) -> Path | None:
    """Find the item path (file or directory) for the given item ID."""
    class_dir = worklog_root / CLASS_MAP[prefix]
    if not class_dir.is_dir():
        return None
    for entry in class_dir.iterdir():
        if entry.is_file() and entry.suffix == ".md" and entry.stem.startswith(item_id):
            return entry
        if entry.is_dir() and entry.name.startswith(item_id):
            return entry
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive a completed worklog item.")
    parser.add_argument("item_id", help="Item ID to archive (e.g. t0001, p0003)")
    parser.add_argument("-w", "--worklog", default="./worklog", help="Worklog root directory (default: ./worklog)")
    parser.add_argument("--force", action="store_true", help="Skip status validation")
    args = parser.parse_args()

    m = ID_RE.match(args.item_id.lower())
    if not m:
        print(f"Error: invalid ID format '{args.item_id}'. Expected t#### or p####.", file=sys.stderr)
        sys.exit(1)

    prefix = m.group(1)
    item_id = m.group(0)

    root = Path(args.worklog).resolve()
    if not root.is_dir():
        print(f"Error: worklog directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    item_path = find_item(root, prefix, item_id)
    if not item_path:
        print(f"Error: no {CLASS_MAP[prefix]} found matching '{item_id}'.", file=sys.stderr)
        sys.exit(1)

    # Determine the frontmatter file to check
    entry_file = item_path if item_path.is_file() else item_path / "index.md"

    # Validate status unless --force
    if not args.force:
        if entry_file.exists():
            item = parse_item(entry_file)
            status = item.get("status", "").lower()
            allowed = DONE_STATUS[prefix]
            if isinstance(allowed, str):
                allowed = (allowed,)
            if status not in allowed:
                allowed_str = " or ".join(f'"{s}"' for s in allowed)
                print(
                    f"Error: {item_id} has status \"{status}\", expected {allowed_str}. "
                    f"Use --force to override.",
                    file=sys.stderr,
                )
                sys.exit(1)

    # Move to archive
    archive_dir = root / "archive" / CLASS_MAP[prefix]
    archive_dir.mkdir(parents=True, exist_ok=True)

    dest = archive_dir / item_path.name
    if dest.exists():
        print(f"Error: archive destination already exists: {dest}", file=sys.stderr)
        sys.exit(1)

    shutil.move(str(item_path), str(dest))
    print(f"Archived {item_path.name} -> archive/{CLASS_MAP[prefix]}/{item_path.name}")


if __name__ == "__main__":
    main()
