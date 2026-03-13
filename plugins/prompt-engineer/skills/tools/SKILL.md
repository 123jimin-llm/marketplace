---
name: tools
description: Use when the user asks to count tokens, measure prompt length, check token usage, run a prompt against an LLM, or test a prompt.
---

# Prompt Tools

## Token Count

Count tokens for a string or file. Report the result to the user.

```bash
python scripts/token-count.py "text"
python scripts/token-count.py -f path/to/file.md
python scripts/token-count.py -f path/to/SKILL.md -s
```

| Flag | Description |
|------|-------------|
| `-f` | Treat input as a file path |
| `-s` | Per-section breakdown (YAML frontmatter + `##` headings). Use when the user wants to find which sections are expensive |
| `-m MODEL` | Model or encoding to count against. Accepts Claude models (`claude-opus-4-6`), OpenAI models (`gpt-5-mini`), or tiktoken encodings (`cl100k_base`). Default: `claude-opus-4-6` |

## Prompt Run

Run a prompt against an LLM. Prints the response to stdout, or JSON with metadata when `--json` is used.

Write prompts to files, then invoke with `-U`/`-S` — keeps prompts reusable and version-controlled. All prompt flags are repeatable; multiple values are joined with double newlines.

```bash
# Quick one-shot
python scripts/invoke-llm.py "What is the capital of France?"

# System + user strings
python scripts/invoke-llm.py "Write a haiku" -s "You are a poet"

# File-based (preferred)
python scripts/invoke-llm.py -U prompt.md -S system.md
python scripts/invoke-llm.py -U prompt.md -S system.md -o output.md

# Compose multiple prompts
python scripts/invoke-llm.py -S role.md -S rules.md -U context.md -U question.md

# Different model
python scripts/invoke-llm.py -U prompt.md -m gpt-5-mini -t 0.0 --json
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

## Dependencies

See `scripts/requirements.txt`. Assume all packages are pre-installed.
