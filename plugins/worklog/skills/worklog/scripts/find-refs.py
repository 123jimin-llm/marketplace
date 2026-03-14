#!/usr/bin/env python3
"""Find all worklog items that reference a given ID.

Usage:
    find-refs.py t0001                  # who references t0001?
    find-refs.py s0002 --include-archive
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
from frontmatter import parse_item, iter_items, _CLASS_PREFIX

# Frontmatter fields that contain cross-references
REF_FIELDS = ("blocked_by", "implements", "modifies", "targets", "updated_by")


def collect_items(worklog_root: Path, include_archive: bool) -> list[dict]:
    """Collect all parseable worklog items."""
    items = []

    scan_dirs = [
        ("task", worklog_root / "task"),
        ("plan", worklog_root / "plan"),
        ("spec", worklog_root / "spec"),
    ]
    if include_archive:
        scan_dirs.extend([
            ("task", worklog_root / "archive" / "task"),
            ("plan", worklog_root / "archive" / "plan"),
        ])

    for item_class, class_dir in scan_dirs:
        prefix = _CLASS_PREFIX[item_class]
        for f in iter_items(class_dir, prefix):
            try:
                items.append(parse_item(f))
            except Exception:
                pass
    return items


def find_references(items: list[dict], target_id: str) -> list[dict]:
    """Find items that reference target_id in frontmatter fields or body."""
    results = []
    target_lower = target_id.lower()
    # Pattern to match the ID as a word boundary in body text
    body_pattern = re.compile(r"\b" + re.escape(target_id) + r"\b", re.IGNORECASE)

    for item in items:
        # Skip self-reference
        if item.get("id", "").lower() == target_lower:
            continue

        found_in = []

        # Check frontmatter reference fields
        for field in REF_FIELDS:
            val = item.get(field, [])
            if isinstance(val, list):
                if any(v.lower() == target_lower for v in val if isinstance(v, str)):
                    found_in.append(f"frontmatter:{field}")
            elif isinstance(val, str) and val.lower() == target_lower:
                found_in.append(f"frontmatter:{field}")

        # Check body text
        body = item.get("_body", "")
        if body_pattern.search(body):
            found_in.append("body")

        if found_in:
            results.append({
                "id": item.get("id", "?"),
                "title": item.get("title", "(untitled)"),
                "path": str(item.get("_path", "?")),
                "found_in": found_in,
            })

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Find items referencing a given ID.")
    parser.add_argument("target_id", help="The ID to search for (e.g. t0001, s0002)")
    parser.add_argument("-w", "--worklog", default="./worklog", help="Worklog root directory (default: ./worklog)")
    parser.add_argument("--include-archive", action="store_true", help="Also search archived items")
    args = parser.parse_args()

    root = Path(args.worklog).resolve()
    if not root.is_dir():
        print(f"Error: worklog directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    items = collect_items(root, args.include_archive)
    refs = find_references(items, args.target_id)

    if not refs:
        print(f"No references to {args.target_id} found.")
        return

    print(f"References to {args.target_id}:\n")
    for ref in refs:
        locations = ", ".join(ref["found_in"])
        print(f"  {ref['id']}  {ref['title']}")
        print(f"         in: {locations}")
        print(f"         at: {ref['path']}")
        print()


if __name__ == "__main__":
    main()
