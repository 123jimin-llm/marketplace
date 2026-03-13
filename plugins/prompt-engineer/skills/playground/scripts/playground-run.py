#!/usr/bin/env python3
"""Run playground prompt variations against inputs. Self-contained — no skill dependencies."""

import argparse
import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from playground import (
    load_playground,
    expand_variations,
    build_run_spec,
    serialize_toml,
)
from util import invoke_llm


def parse_variation_flags(flags: list[str] | None) -> dict[str, list[str]]:
    """Parse -v SLOT=VAR[,VAR,...] flags into {slot: [var, ...]}."""
    result = {}
    for flag in (flags or []):
        if "=" not in flag:
            print(f"Error: variation flag must be SLOT=VAR[,VAR,...]: {flag!r}", file=sys.stderr)
            sys.exit(1)
        slot, values = flag.split("=", 1)
        result[slot] = [v.strip() for v in values.split(",")]
    return result


def combo_label(combo: dict[str, str]) -> str:
    """Build a filesystem-safe label from a variation combo."""
    parts = [f"{k}={v}" for k, v in sorted(combo.items())]
    return ",".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Run playground prompt variations against inputs.",
    )
    parser.add_argument(
        "playground_dir",
        help="Path to playground root directory",
    )
    parser.add_argument(
        "-l", "--label",
        help="Run label (required unless --dry-run)",
    )
    parser.add_argument(
        "-v", "--variation",
        action="append", dest="variations",
        help="Set slot variations: SLOT=VAR[,VAR,...]. Repeatable. * sweeps all.",
    )
    parser.add_argument(
        "-i", "--inputs",
        help="Filter inputs by name pattern (e.g., 'case*'). Default: all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated TOMLs to stdout without executing.",
    )
    parser.add_argument(
        "--json",
        action="store_true", dest="json_output",
        help="Include metadata (tokens, latency) in output frontmatter.",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.label:
        parser.error("-l/--label is required unless --dry-run")

    # 1. Load playground
    pg_dir = Path(args.playground_dir)
    if not pg_dir.is_dir():
        print(f"Error: not a directory: {pg_dir}", file=sys.stderr)
        sys.exit(1)

    pg = load_playground(pg_dir)

    # 2. Parse variations
    variation_spec = parse_variation_flags(args.variations)
    combos = expand_variations(pg, variation_spec)

    # 3. Filter inputs
    inputs = pg["inputs"]
    if args.inputs:
        inputs = [p for p in inputs if fnmatch.fnmatch(p.stem, args.inputs)]
        if not inputs:
            print(f"Error: no inputs match pattern: {args.inputs!r}", file=sys.stderr)
            sys.exit(1)

    if not inputs:
        print("Error: no input files found in inputs/", file=sys.stderr)
        sys.exit(1)

    multi_combo = len(combos) > 1
    total = len(combos) * len(inputs)
    count = 0

    for combo in combos:
        c_label = combo_label(combo)

        for input_file in inputs:
            count += 1
            case_name = input_file.stem
            print(f"[{count}/{total}] {c_label} / {case_name}", file=sys.stderr)

            spec = build_run_spec(pg, combo, input_file)

            if args.dry_run:
                print(f"# --- {c_label} / {case_name} ---")
                print(serialize_toml(spec["toml_dict"]))
                continue

            # Execute LLM call
            try:
                result = invoke_llm(
                    spec["user_message"],
                    system=spec["system"],
                    model=spec["model"],
                    temperature=spec["temperature"],
                    max_tokens=spec["max_tokens"],
                )
            except Exception as e:
                print(f"  ERROR: {e}", file=sys.stderr)
                continue

            # Determine output path
            out_base = pg["pg_dir"] / "outputs" / args.label
            if multi_combo:
                out_dir = out_base / c_label
            else:
                out_dir = out_base
            out_dir.mkdir(parents=True, exist_ok=True)

            # Write output file
            out_file = out_dir / f"{case_name}.md"
            fm_lines = []
            if args.json_output:
                fm_lines.append(f'model = "{result["model"]}"')
                fm_lines.append(f'input_tokens = {result["input_tokens"]}')
                fm_lines.append(f'output_tokens = {result["output_tokens"]}')
                fm_lines.append(f'latency_ms = {result["latency_ms"]}')
                fm_lines.append(f'stop_reason = "{result["stop_reason"]}"')

            content = ""
            if fm_lines:
                content = "+++\n" + "\n".join(fm_lines) + "\n+++\n"
            content += result["response"] + "\n"
            out_file.write_text(content, encoding="utf-8")

            print(f"  → {out_file.relative_to(pg['pg_dir'])}", file=sys.stderr)

        # Save run.toml per combo
        if not args.dry_run:
            out_base = pg["pg_dir"] / "outputs" / args.label
            if multi_combo:
                toml_dir = out_base / c_label
            else:
                toml_dir = out_base
            toml_dir.mkdir(parents=True, exist_ok=True)

            # Use the last input to generate a representative run.toml
            # (paths are relative anyway — the TOML captures the composition structure)
            if inputs:
                last_spec = build_run_spec(pg, combo, inputs[0])
                toml_path = toml_dir / "run.toml"
                toml_path.write_text(serialize_toml(last_spec["toml_dict"]), encoding="utf-8")

    if not args.dry_run:
        print(f"\nDone. {count} outputs written to outputs/{args.label}/", file=sys.stderr)


if __name__ == "__main__":
    main()
