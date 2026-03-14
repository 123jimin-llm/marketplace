#!/usr/bin/env python3
"""Invoke an LLM with a prompt. Supports Claude (Anthropic) and OpenAI models."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from util import invoke_llm, read_input, toml_str


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


def _result_to_toml(result: dict) -> str:
    """Serialize a single LLM result dict to a TOML document string."""
    lines = [
        f"response = {toml_str(result['response'], multiline=True)}",
        f"model = {toml_str(result['model'])}",
        f"input_tokens = {result['input_tokens']}",
        f"output_tokens = {result['output_tokens']}",
        f"latency_ms = {result['latency_ms']}",
        f"stop_reason = {toml_str(result['stop_reason'])}",
    ]
    return "\n".join(lines) + "\n"


def _results_to_toml(results: list) -> str:
    """Serialize matrix results to a TOML document with [[results]] array of tables."""
    parts = []
    for r in results:
        labels = r["labels"]
        label_items = ", ".join(f'{k} = {toml_str(str(v))}' for k, v in labels.items())
        lines = [
            "[[results]]",
            f"labels = {{{label_items}}}",
        ]
        if "error" in r:
            lines.append(f"error = {toml_str(r['error'], multiline=True)}")
        else:
            lines += [
                f"response = {toml_str(r['response'], multiline=True)}",
                f"model = {toml_str(r['model'])}",
                f"input_tokens = {r['input_tokens']}",
                f"output_tokens = {r['output_tokens']}",
                f"latency_ms = {r['latency_ms']}",
                f"stop_reason = {toml_str(r['stop_reason'])}",
            ]
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


def run_matrix(config_path, dry_run, json_output, toml_output, overrides=None):
    """Run a TOML-configured matrix of LLM invocations."""
    from matrix import load_config, expand_matrix, matrix_dimensions
    from display import render_table

    config = load_config(config_path)

    # Apply CLI overrides to [generation] — replaces config values entirely
    if overrides:
        gen = config.setdefault("generation", {})
        for key, value in overrides.items():
            gen[key] = value
    output_file = config.get("output", {}).get("file")

    if dry_run:
        info = matrix_dimensions(config)
        print(f"Total runs: {info['total_runs']}")
        if info["dimensions"]:
            print("\nSweep dimensions:")
            for dim, values in info["dimensions"].items():
                print(f"  {dim}: {values}")
        else:
            print("No sweep dimensions (single run)")
        return

    runs = expand_matrix(config)
    results = []

    for i, spec in enumerate(runs):
        labels = spec["labels"]
        label_str = ", ".join(f"{k}={v}" for k, v in labels.items())
        print(f"[{i+1}/{len(runs)}] {label_str}", file=sys.stderr)

        try:
            result = invoke_llm(
                spec["user_message"],
                system=spec["system"],
                model=spec["model"],
                temperature=spec["temperature"],
                max_tokens=spec["max_tokens"],
            )
            record = {"labels": labels, **result}
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            record = {"labels": labels, "error": str(e)}

        results.append(record)

    # Write output file if configured
    if output_file:
        base_dir = config["_base_dir"]
        out_path = base_dir / output_file
        use_toml = toml_output or out_path.suffix == ".toml"
        with open(out_path, "w", encoding="utf-8") as f:
            if use_toml:
                f.write(_results_to_toml(results))
            else:
                for r in results:
                    f.write(json.dumps(r) + "\n")
        print(f"\nResults written to {out_path}", file=sys.stderr)

    # Structured output to stdout
    if toml_output:
        print(_results_to_toml(results), end="")
    elif json_output:
        for r in results:
            print(json.dumps(r))
    else:
        # Print summary table
        columns = ["model", "temp", "in_tok", "out_tok", "latency", "stop"]
        rows = []
        for r in results:
            labels = r["labels"]
            # Build row label from prompt labels
            parts = []
            if "system" in labels:
                parts.append(labels["system"])
            parts.append(labels["user"])
            row_label = "  ".join(parts) if len(parts) > 1 else parts[0]

            if "error" in r:
                rows.append((row_label, labels["model"], str(labels["temperature"]),
                             "-", "-", "-", "ERROR"))
            else:
                rows.append((
                    row_label,
                    r["model"],
                    str(labels["temperature"]),
                    str(r["input_tokens"]),
                    str(r["output_tokens"]),
                    str(r["latency_ms"]),
                    r["stop_reason"],
                ))

        if rows:
            print(file=sys.stderr)
            render_table(rows, columns)


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
        default=None,
        help="Model ID (default: claude-sonnet-4-6; overrides config in -c mode)",
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=None,
        help="Temperature (default: 1.0; overrides config in -c mode)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Max output tokens (default: 4096; overrides config in -c mode)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Write output to file",
    )
    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output JSON with metadata (response, model, tokens, latency, stop_reason)",
    )
    fmt_group.add_argument(
        "--toml",
        action="store_true",
        dest="toml_output",
        help="Output TOML with metadata (response, model, tokens, latency, stop_reason)",
    )
    parser.add_argument(
        "-c", "--config",
        help="TOML config file for matrix/batch runs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print matrix dimensions without executing (requires -c)",
    )
    args = parser.parse_args()

    # Validate --dry-run requires -c
    if args.dry_run and not args.config:
        parser.error("--dry-run requires -c/--config")

    # TOML config mode
    if args.config:
        # Prompt flags are mutually exclusive with config mode
        single_shot_used = any([
            args.input, args.user_strings, args.user_files,
            args.system_strings, args.system_files,
        ])
        if single_shot_used:
            parser.error("-c/--config is mutually exclusive with positional, -u, -U, -s, -S")

        if args.output:
            print("Warning: -o ignored in config mode (use [output].file in TOML)", file=sys.stderr)

        # Collect generation overrides from CLI flags
        overrides = {}
        if args.model is not None:
            overrides["model"] = args.model
        if args.temperature is not None:
            overrides["temperature"] = args.temperature
        if args.max_tokens is not None:
            overrides["max_tokens"] = args.max_tokens

        run_matrix(args.config, args.dry_run, args.json_output, args.toml_output, overrides or None)
        return

    # --- Single-shot mode ---

    # Apply defaults for single-shot mode
    model = args.model or "claude-sonnet-4-6"
    temperature = args.temperature if args.temperature is not None else 1.0
    max_tokens = args.max_tokens or 4096

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
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.toml_output:
        output = _result_to_toml(result)
    elif args.json_output:
        output = json.dumps(result, indent=2)
    else:
        output = result["response"]

    print(output)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")


if __name__ == "__main__":
    main()
