---
name: tools
description: Use when the user asks to count tokens, measure prompt length, check token usage, run a prompt against an LLM, or test a prompt.
---

# Prompt Tools

## Available scripts

- **`scripts/token-count.py`** — Count tokens in a string or file.
- **`scripts/invoke-llm.py`** — Run a prompt against an LLM and return the response.

## Token Count

Count tokens for a string or file. Report the result to the user.

```bash
python scripts/token-count.py "text"
python scripts/token-count.py -f path/to/file.md
python scripts/token-count.py -f path/to/SKILL.md -s
```

### Flags

| Flag | Description |
|------|-------------|
| `-f` | Treat input as a file path |
| `-s` | Per-section breakdown (YAML frontmatter + `##` headings). Use when the user wants to find which sections are expensive |
| `-m MODEL` | Model or encoding to count against. Accepts Claude models (`claude-opus-4-6`), OpenAI models (`gpt-5-mini`), or tiktoken encodings (`cl100k_base`). Defaults to `claude-opus-4-6` |

## Prompt Run

Run a prompt against an LLM. Prints the response to stdout, or JSON with metadata when `--json` is used.

All flags that accept strings (`-u`, `-s`) have file variants (`-U`, `-S`). **Prefer file inputs** — write prompts to files first, then invoke with `-f`/`-S`. This makes commands reusable across iterations and keeps prompts version-controlled.

All prompt flags are repeatable. Multiple values are joined with double newlines.

```bash
# Quick one-shot
python scripts/invoke-llm.py "What is the capital of France?"

# System + user strings
python scripts/invoke-llm.py "Write a haiku" -s "You are a poet"

# File-based (preferred for iteration)
python scripts/invoke-llm.py -U prompt.md -S system.md
python scripts/invoke-llm.py -U prompt.md -S system.md -o output.md

# Compose multiple prompts
python scripts/invoke-llm.py -S role.md -S rules.md -U context.md -U question.md

# Different model
python scripts/invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --json
```

### Flags

| Flag | Description |
|------|-------------|
| `-u TEXT` | User prompt string (repeatable) |
| `-U FILE` | User prompt from file (repeatable) |
| `-s TEXT` | System prompt string (repeatable) |
| `-S FILE` / `--system-file` | System prompt from file (repeatable) |
| `-m MODEL` | Model ID. Claude models use Anthropic API, others use OpenAI API. Default: `claude-sonnet-4-6` |
| `-t TEMP` | Temperature (default: `1.0`) |
| `--max-tokens N` | Max output tokens (default: `4096`) |
| `-o FILE` / `--output` | Write output to file (still prints to stdout) |
| `--json` | JSON output with full metadata (response, model, tokens, latency, stop_reason) |

A positional argument is also accepted as a convenience shorthand for `-u`.

## Dependencies

See `scripts/requirements.txt`. Assume all packages are pre-installed.
