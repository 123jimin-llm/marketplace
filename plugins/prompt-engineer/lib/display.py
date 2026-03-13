"""Display utilities for prompt-engineer scripts — table rendering, input collection."""

import os
import sys


def collect_inputs(
    strings: list[str] | None = None,
    files: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Build (label, text) pairs from string args and file paths.

    Exits with an error message if a file is not found.
    """
    items: list[tuple[str, str]] = []
    for s in strings or []:
        label = s if len(s) <= 40 else s[:37] + "..."
        items.append((label, s))
    for path in files or []:
        try:
            text = open(path, encoding="utf-8").read()
        except FileNotFoundError:
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        items.append((os.path.basename(path), text))
    return items


def render_table(
    rows: list[tuple[str, ...]],
    columns: list[str],
    separator_before: int | None = None,
):
    """Print a right-aligned table.

    Args:
        rows: Each row is (label, val1, val2, ...) matching len(columns).
        columns: Column header names.
        separator_before: If set, print a separator line before this row index.
    """
    label_width = max(len(row[0]) for row in rows)
    col_widths = [max(len(c), 7) for c in columns]

    # Header
    header = f"  {'':>{label_width}}"
    for col, w in zip(columns, col_widths):
        header += f"  {col:>{w}}"
    print(header)

    # Rows
    for i, row in enumerate(rows):
        if separator_before is not None and i == separator_before:
            sep = f"  {'':─>{label_width}}"
            for w in col_widths:
                sep += f"──{'':─>{w}}"
            print(sep)
        line = f"  {row[0]:>{label_width}}"
        for val, w in zip(row[1:], col_widths):
            line += f"  {val:>{w}}"
        print(line)
