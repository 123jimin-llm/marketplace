---
name: invoke-llm
description: This skill should be used when the user asks to run a prompt against an LLM, invoke Claude or OpenAI, test a prompt, get a completion, compose prompts from files, run a matrix sweep, or batch-test prompts across models/temperatures.
---

# Invoke LLM

Run a prompt against an LLM. Prints the response to stdout, or JSON with metadata when `--json` is used.

All prompt flags are repeatable; multiple values are joined with double newlines. Write prompts to files, then invoke with `-U`/`-S`.

Script: `scripts/invoke-llm.py`

## Single-shot mode

```bash
invoke-llm.py "What is the capital of France?"
invoke-llm.py "Write a haiku" -s "You are a poet"
invoke-llm.py -U prompt.md -S system.md -o output.md
invoke-llm.py -S role.md -S rules.md -U context.md -U question.md
invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --json
```

| Flag | Description |
|------|-------------|
| (positional) | User prompt string (shorthand for `-u`) |
| `-u TEXT` | User prompt string (repeatable) |
| `-U FILE` | User prompt from file (repeatable) |
| `-s TEXT` | System prompt string (repeatable) |
| `-S FILE` | System prompt from file (repeatable) |
| `-m MODEL` | Model ID. Claude → Anthropic API; others → OpenAI API. Default: `claude-sonnet-4-6` |
| `-t TEMP` | Temperature. Default: `1.0` |
| `--max-tokens N` | Max output tokens. Default: `4096` |
| `-o FILE` | Write output to file (still prints to stdout) |
| `--json` | JSON output with metadata (response, model, tokens, latency, stop_reason) |

## TOML config mode

Use `-c` with a TOML file for cleaner invocation and matrix sweeps across models, temperatures, and prompt variations.

```bash
invoke-llm.py -c run.toml                   # run from config
invoke-llm.py -c run.toml --dry-run         # print matrix shape, don't execute
invoke-llm.py -c run.toml --json            # JSONL output to stdout
```

| Flag | Description |
|------|-------------|
| `-c FILE` | TOML config file. Mutually exclusive with positional, `-u`, `-U`, `-s`, `-S`, `-m`, `-t`, `--max-tokens` |
| `--dry-run` | Print matrix dimensions and total run count without executing (requires `-c`) |

### TOML schema

```toml
[generation]
model = "claude-sonnet-4-6"          # scalar = fixed, array = sweep
temperature = 1.0
max_tokens = 4096

[[prompts]]
role = "system"                       # "system" or "user"
file = ["strict.md", "relaxed.md"]    # array = sweep dimension
# OR: prompt = "inline text"          # file and prompt are mutually exclusive

[[prompts]]
role = "user"
file = "context.md"                   # multiple entries with same role = concatenation

[[prompts]]
role = "user"
file = "question.md"

[output]
file = "results.jsonl"                # optional, JSONL output
```

**Rules:**

- `[generation]`: scalar = fixed value, array = sweep dimension. Cartesian product of all arrays.
- `[[prompts]]`: each entry has `role` + exactly one of `file` or `prompt`. Multiple entries with the same role are concatenated (double newline). Array value in `file`/`prompt` = sweep dimension.
- `[output]`: optional. If `file` is set, write JSONL there.
- File paths are relative to the TOML file's parent directory.

**Matrix = cartesian product of:** `model[]` × `temperature[]` × each `[[prompts]]` entry's array values.

### Example: single run via TOML

```toml
[generation]
model = "claude-sonnet-4-6"
temperature = 0.5

[[prompts]]
role = "system"
file = "system.md"

[[prompts]]
role = "user"
file = "question.md"
```

### Example: matrix sweep

```toml
[generation]
model = ["claude-sonnet-4-6", "gpt-5-mini"]
temperature = [0.0, 0.5, 1.0]

[[prompts]]
role = "system"
file = ["strict.md", "relaxed.md"]

[[prompts]]
role = "user"
file = "question.md"

[output]
file = "results.jsonl"
```

This produces 2 × 3 × 2 = 12 runs. Each result is written as a JSONL line:

```json
{"labels":{"model":"claude-sonnet-4-6","temperature":0.5,"system":"strict.md","user":"question.md"},"response":"...","model":"claude-sonnet-4-6","input_tokens":142,"output_tokens":387,"latency_ms":1204,"stop_reason":"end_turn"}
```

A summary table is printed to stderr after all runs complete.

## Dependencies

`anthropic`, `openai` — assume pre-installed.
