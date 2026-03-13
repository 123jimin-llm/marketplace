#!/usr/bin/env python3
"""Invoke an LLM with a prompt. Supports Claude (Anthropic) and OpenAI models."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from util import invoke_llm, read_input


def collect_parts(strings, files):
    """Collect prompt parts from string args and file args, in order. Returns joined text or None."""
    parts = []
    for s in (strings or []):
        parts.append(s)
    for f in (files or []):
        try:
            parts.append(read_input(f, is_file=True))
        except FileNotFoundError:
            print(f"File not found: {f}", file=sys.stderr)
            sys.exit(1)
    return "\n\n".join(parts) if parts else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", nargs="?", default=None,
        help="User prompt string (convenience shorthand for -u)",
    )
    parser.add_argument(
        "-u", "--user",
        action="append", dest="user_strings",
        help="User prompt string (repeatable)",
    )
    parser.add_argument(
        "-U", "--user-file",
        action="append", dest="user_files",
        help="User prompt from file (repeatable)",
    )
    parser.add_argument(
        "-s", "--system",
        action="append", dest="system_strings",
        help="System prompt string (repeatable)",
    )
    parser.add_argument(
        "-S", "--system-file",
        action="append", dest="system_files",
        help="System prompt from file (repeatable)",
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-sonnet-4-6",
        help="Model ID (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=1.0,
        help="Temperature (default: 1.0)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max output tokens (default: 4096)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Write output to file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output JSON with metadata",
    )
    args = parser.parse_args()

    # Build user message: positional first, then -u strings, then -U files
    user_strings = []
    if args.input:
        user_strings.append(args.input)
    user_strings.extend(args.user_strings or [])
    user_message = collect_parts(user_strings, args.user_files)

    if not user_message:
        print("No user prompt provided. Use positional arg, -u, or -U.", file=sys.stderr)
        sys.exit(1)

    # Build system message: -s strings, then -S files
    system = collect_parts(args.system_strings, args.system_files)

    try:
        result = invoke_llm(
            user_message,
            system=system,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json_output:
        output = json.dumps(result, indent=2)
    else:
        output = result["response"]

    print(output)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")


if __name__ == "__main__":
    main()
