#!/usr/bin/env python3
"""Count tokens in strings or files. Supports Claude, OpenAI, and tiktoken encodings."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from display import collect_inputs, render_table
from util import count_tokens, split_frontmatter, split_sections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs", nargs="*",
        help="Strings to count tokens for",
    )
    parser.add_argument(
        "-f", "--file",
        action="append", dest="files",
        help="File path to count tokens for (repeatable)",
    )
    parser.add_argument(
        "-m", "--model",
        action="append", dest="models",
        help="Model or encoding (repeatable). Default: claude-opus-4-6",
    )
    parser.add_argument(
        "-s", "--sections",
        action="store_true",
        help="Break down by YAML frontmatter description and ## sections",
    )
    args = parser.parse_args()

    models = args.models or ["claude-opus-4-6"]
    items = collect_inputs(args.inputs, args.files)

    if not items:
        print("No inputs provided. Pass strings or use -f.", file=sys.stderr)
        sys.exit(1)

    multi = len(items) > 1 or len(models) > 1

    try:
        if multi:
            _print_table(items, models, args.sections)
        else:
            _print_single(items[0], models[0], args.sections)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _count_row(label: str, text: str, models: list[str]) -> tuple[str, ...]:
    """Build a table row: (label, count_for_model_1, count_for_model_2, ...)."""
    return (label, *(str(count_tokens(text, m)) for m in models))


def _print_single(item: tuple[str, str], model: str, sections: bool):
    """Compact single-input display."""
    _, text = item
    lines = text.count("\n")
    total = count_tokens(text, model)

    if sections:
        description, _, body = split_frontmatter(text)
        parts = []
        if description:
            parts.append(("(description)", description))
        parts.extend(split_sections(body))

        max_name = max(len(name) for name, _ in parts) if parts else 0
        for name, content in parts:
            t = count_tokens(content, model)
            print(f"  {name:<{max_name}}  {t:>5} tokens")
        print(f"  {'':─<{max_name}}──{'':─>7}")

    print(f"  {total} tokens, {lines} lines  [{model}]")


def _print_table(items: list[tuple[str, str]], models: list[str], sections: bool):
    """Multi-input and/or multi-model table display."""
    if sections and len(items) == 1:
        _, text = items[0]
        description, _, body = split_frontmatter(text)
        parts = []
        if description:
            parts.append(("(description)", description))
        parts.extend(split_sections(body))

        rows = [_count_row(name, content, models) for name, content in parts]
        rows.append(_count_row("TOTAL", text, models))
        render_table(rows, models, separator_before=len(rows) - 1)
        return

    rows = [_count_row(label, text, models) for label, text in items]
    render_table(rows, models)


if __name__ == "__main__":
    main()
