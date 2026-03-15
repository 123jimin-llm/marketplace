#!/usr/bin/env python3
"""List worklog items by type, with optional status and tag filters.

Usage:
    list.py task                    # all tasks
    list.py task -s active          # active tasks only
    list.py spec -t auth            # specs tagged "auth"
    list.py plan --json             # JSON output
"""

import argparse
import json
import sys
from pathlib import Path

from _frontmatter import parse_item, iter_items, CLASS_PREFIX

CLASS_MAP = {"task": "task", "plan": "plan", "spec": "spec"}


def find_items(worklog_root: Path, item_class: str) -> list[dict]:
    """Find and parse all items of the given class."""
    class_dir = worklog_root / CLASS_MAP[item_class]
    prefix = CLASS_PREFIX[item_class]
    items = []
    for f in iter_items(class_dir, prefix):
        try:
            items.append(parse_item(f))
        except Exception as e:
            print(f"Warning: failed to parse {f}: {e}", file=sys.stderr)
    return items


def filter_items(items: list[dict], status: str | None, tag: str | None) -> list[dict]:
    """Apply optional status and tag filters."""
    if status:
        items = [i for i in items if i.get("status", "").lower() == status.lower()]
    if tag:
        items = [i for i in items if tag.lower() in [t.lower() for t in i.get("tags", [])]]
    return items


def print_table(items: list[dict], item_class: str) -> None:
    """Print items as an aligned table."""
    if not items:
        print(f"No {item_class} items found.")
        return

    has_status = item_class in ("task", "plan")
    header_parts = ["ID", "Title"]
    if has_status:
        header_parts.append("Status")
    header_parts.append("Tags")

    rows: list[list[str]] = []
    for item in items:
        row = [
            item.get("id", "?"),
            item.get("title", "(untitled)"),
        ]
        if has_status:
            row.append(item.get("status", "?"))
        row.append(", ".join(item.get("tags", [])) or "-")
        rows.append(row)

    # Calculate column widths
    widths = [len(h) for h in header_parts]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # Print
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*header_parts))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def print_json(items: list[dict]) -> None:
    """Print items as JSON, excluding internal keys."""
    clean = []
    for item in items:
        d = {k: v for k, v in item.items() if not k.startswith("_")}
        # Convert Path to string and date to ISO string
        for k, v in d.items():
            if hasattr(v, "__fspath__"):
                d[k] = str(v)
            elif hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        clean.append(d)
    print(json.dumps(clean, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="List worklog items.")
    parser.add_argument("item_class", choices=CLASS_MAP.keys(), help="Item class: task, plan, or spec")
    parser.add_argument("-s", "--status", help="Filter by status")
    parser.add_argument("-t", "--tag", help="Filter by tag")
    parser.add_argument("-w", "--worklog", default="./worklog", help="Worklog root directory (default: ./worklog)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    root = Path(args.worklog).resolve()
    if not root.is_dir():
        print(f"Error: worklog directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    items = find_items(root, args.item_class)
    items = filter_items(items, args.status, args.tag)

    if args.json:
        print_json(items)
    else:
        print_table(items, args.item_class)


if __name__ == "__main__":
    main()
