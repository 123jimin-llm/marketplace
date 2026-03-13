#!/usr/bin/env python3
"""Count tokens in a string or file. Supports Claude, OpenAI, and tiktoken encodings."""

import argparse
import sys

from util import count_tokens, split_frontmatter, split_sections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="String to count, or file path with -f")
    parser.add_argument(
        "-f", "--file",
        action="store_true",
        help="Treat input as a file path",
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-opus-4-6",
        help="Claude model (claude-opus-4-6), OpenAI model (gpt-5-mini), or tiktoken encoding (cl100k_base)",
    )
    parser.add_argument(
        "-s", "--sections",
        action="store_true",
        help="Break down by YAML frontmatter description and ## sections",
    )
    args = parser.parse_args()

    if args.file:
        try:
            text = open(args.input, encoding="utf-8").read()
        except FileNotFoundError:
            print(f"File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        text = args.input

    try:
        lines = text.count("\n")
        total = count_tokens(text, args.model)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.sections:
        description, _, body = split_frontmatter(text)
        parts = []
        if description:
            parts.append(("(description)", description))
        parts.extend(split_sections(body))

        max_name = max(len(name) for name, _ in parts) if parts else 0
        for name, content in parts:
            t = count_tokens(content, args.model)
            print(f"  {name:<{max_name}}  {t:>5} tokens")
        print(f"  {'':─<{max_name}}──{'':─>7}")

    print(f"  {total} tokens, {lines} lines  [{args.model}]")


if __name__ == "__main__":
    main()
