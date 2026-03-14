#!/usr/bin/env python3
"""Validate worklog integrity: references, statuses, required fields.

Usage:
    validate.py                         # check ./worklog
    validate.py -w path/to/worklog      # check specific worklog
    validate.py --strict                # treat warnings as errors
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
from frontmatter import (
    CLASS_PREFIX,
    collect_all_items,
    iter_items,
    parse_item,
    scan_ids,
)

TASK_STATUSES = {"pending", "active", "blocked", "done"}
PLAN_STATUSES = {"draft", "approved", "active", "abandoned"}
REQUIRED_FIELDS = ("id", "title", "created")
REF_FIELDS = ("blocked_by", "implements", "modifies", "targets", "updated_by")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate worklog integrity.")
    parser.add_argument("-w", "--worklog", default="./worklog", help="Worklog root directory (default: ./worklog)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    root = Path(args.worklog).resolve()
    if not root.is_dir():
        print(f"Error: worklog directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    errors: list[str] = []
    warnings: list[str] = []

    # Collect all items, reporting parse failures
    items: list[dict] = []
    for cls in ("task", "plan", "spec"):
        prefix = CLASS_PREFIX[cls]
        class_dir = root / cls
        for f in iter_items(class_dir, prefix):
            try:
                items.append(parse_item(f))
            except Exception as e:
                errors.append(f"Parse error in {f}: {e}")

    # Build lookup: id -> item
    active_ids: dict[str, dict] = {}
    for item in items:
        item_id = item.get("id", "")
        if item_id:
            active_ids[item_id.lower()] = item

    # Build archive ID set for dangling ref checks
    archive_ids: set[str] = set()
    for cls in ("task", "plan"):
        prefix = CLASS_PREFIX[cls]
        for num in scan_ids(root, prefix):
            full_id = f"{prefix}{num:04d}"
            if full_id not in active_ids:
                archive_ids.add(full_id)

    # Check each item
    for item in items:
        path = item.get("_path", "?")
        item_id = item.get("id", "")
        item_class = ""
        if item_id:
            prefix_char = item_id[0].lower()
            class_map = {"t": "task", "p": "plan", "s": "spec"}
            item_class = class_map.get(prefix_char, "")

        # Required fields
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"{item_id or path}: missing required field '{field}'")

        # Status required for tasks/plans
        if item_class in ("task", "plan") and "status" not in item:
            errors.append(f"{item_id}: missing required field 'status'")

        # ID-filename mismatch
        if item_id:
            fname = path.stem if path.name != "index.md" else path.parent.name
            if not str(fname).startswith(item_id):
                errors.append(f"{item_id}: id does not match filename '{fname}'")

        # Status validation
        status = item.get("status", "")
        if item_class == "task" and status and status.lower() not in TASK_STATUSES:
            errors.append(f"{item_id}: invalid task status '{status}'")
        elif item_class == "plan" and status and status.lower() not in PLAN_STATUSES:
            errors.append(f"{item_id}: invalid plan status '{status}'")
        elif item_class == "spec" and "status" in item:
            warnings.append(f"{item_id}: specs should not have a status field")

        # Dangling references
        for field in REF_FIELDS:
            refs = item.get(field, [])
            if isinstance(refs, str):
                refs = [refs]
            if not isinstance(refs, list):
                continue
            for ref in refs:
                ref_lower = ref.lower()
                if ref_lower not in active_ids and ref_lower not in archive_ids:
                    errors.append(f"{item_id}: dangling reference {ref} in {field}")
                elif ref_lower not in active_ids and ref_lower in archive_ids:
                    warnings.append(f"{item_id}: {field} references archived item {ref}")

        # Stale blocked_by
        for ref in item.get("blocked_by", []):
            if not isinstance(ref, str):
                continue
            blocker = active_ids.get(ref.lower())
            if blocker:
                blocker_status = blocker.get("status", "").lower()
                if blocker_status in ("done", "abandoned"):
                    warnings.append(f"{item_id}: blocked_by {ref} which has status '{blocker_status}'")

    # Archivable plans: all implementing tasks are done/archived
    plans = [i for i in items if i.get("id", "")[0:1].lower() == "p"]
    for plan in plans:
        plan_id = plan.get("id", "").lower()
        plan_status = plan.get("status", "").lower()
        if plan_status not in ("active", "approved"):
            continue
        # Find tasks that implement this plan
        implementing = [
            i for i in items
            if plan_id in [x.lower() for x in i.get("implements", []) if isinstance(x, str)]
        ]
        if implementing and all(
            i.get("status", "").lower() == "done"
            or i.get("id", "").lower() in archive_ids
            for i in implementing
        ):
            warnings.append(f"{plan.get('id')}: all implementing tasks are complete — consider archiving")

    # Report
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")

    total_errors = len(errors) + (len(warnings) if args.strict else 0)
    total = len(items)
    print(f"\n{total} items checked: {len(errors)} errors, {len(warnings)} warnings")

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
